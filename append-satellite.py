# MQTT Settings V1.0 by simonsaystechtalk @11-2-2025 
# This is still a work in progress!
# Use this to create a mediaplayer in homeassistant, thats the goal.
# Manually enter mqtt broker ip and username and password.
# To get this working some additional packages are required.
# pip install paho-mqtt asyncio numpy wave
# sudo apt install -y python3 python3-venv python3-pip git mpg123 mosquitto-clients
# Append this code to satellite.py
# Use: mosquitto_pub -h YOURIPADDRESS -u USERNAME -P PASSWORD -t "test/topic" -m "Hello from Wyoming #Satellite"
# mosquitto_sub -h YOURIPADDRESS -u USERNAME -P PASSWORD -t "test/topic"
# mosquitto_pub -h YOURIPADDRESS -u USERNAME -P PASSWORD -t "homeassistant/media_player/wyoming_satellite/command" \
#  -m '{"command": "play_media", "media_content_id": "file:///YOURPATH/sounds/#awake.wav"}'
#Put this at the beginning of satellite.py
#import paho.mqtt.client as mqtt
#import json
#import array
#import asyncio
#import math
#import time
#import wave
#import logging
#import os
#import subprocess
#import threading


MQTT_BROKER = "YOUR IP ADDRESS"
MQTT_PORT = 1883
MQTT_TOPIC_MEDIA = "homeassistant/media_player/wyoming_satellite"
MQTT_COMMAND_TOPIC = f"{MQTT_TOPIC_MEDIA}/command"
MQTT_STATE_TOPIC = f"{MQTT_TOPIC_MEDIA}/state"
MQTT_AVAILABILITY_TOPIC = f"{MQTT_TOPIC_MEDIA}/available"
MQTT_DISCOVERY_TOPIC = f"{MQTT_TOPIC_MEDIA}/config"
MQTT_TTS = "wyoming-satellite/tts"

# Initialize MQTT Client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set("USERNAME", "PASSWORD")

# Define playback control
current_state = "idle"
volume = 1.0  # Default volume (1.0 = 100%)

def send_discovery():
    """Send MQTT discovery message for Home Assistant"""
    config_payload = {
        "name": "Wyoming Satellite",
        "command_topic": MQTT_COMMAND_TOPIC,
        "state_topic": MQTT_STATE_TOPIC,
        "availability_topic": MQTT_AVAILABILITY_TOPIC,
        "payload_available": "online",
        "payload_not_available": "offline",
        "unique_id": "wyoming_satellite",
        "platform": "mqtt"
    }
    client.publish(MQTT_DISCOVERY_TOPIC, json.dumps(config_payload), retain=True)
    logging.info("📢 Sent MQTT Discovery message to Home Assistant")

async def play_audio(file_path: str):
    """Play audio file asynchronously using aplay."""
    if os.path.exists(file_path):
        logging.info(f"🔊 Playing audio file: {file_path}")
        process = await asyncio.create_subprocess_exec(
            "aplay", "-D", "plughw:CARD=MS,DEV=0", file_path,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            logging.info(f"✅ Successfully played: {file_path}")
        else:
            logging.error(f"❌ Error playing {file_path}: {stderr.decode().strip()}")
    else:
        logging.error(f"❌ File not found: {file_path}")

def on_connect(client, userdata, flags, rc, properties=None):
    """Callback for when the client connects to the broker"""
    if rc == 0:
        logging.info("✅ Successfully connected to MQTT broker")
        client.subscribe(MQTT_COMMAND_TOPIC, qos=0)
        client.subscribe(MQTT_TTS, qos=0)
        logging.info("✅ Subscribed to: MQTT command & TTS topics")
    else:
        logging.error(f"❌ Failed to connect to MQTT broker. Return code: {rc}")

def update_media_state():
    """Update MQTT with the current media player state."""
    state_payload = {
        "state": current_state,
        "attributes": {"volume_level": volume},
    }
    client.publish(MQTT_STATE_TOPIC, json.dumps(state_payload), retain=True)
    logging.debug(f"📢 Published state update: {state_payload}")

def on_message(client, userdata, msg):
    """Handle incoming MQTT messages"""
    global current_state, volume
    logging.debug(f"📩 Received MQTT message: {msg.topic} -> {msg.payload.decode()}")
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        if msg.topic == MQTT_TTS:
            text = payload.get("text", "")
            logging.info(f"🎙️ TTS Received: {text}")
            subprocess.run(["aplay", "/usr/share/sounds/alsa/Front_Center.wav"])
        elif msg.topic == MQTT_COMMAND_TOPIC:
            command = payload.get("command", "")
            logging.debug(f"🔍 Parsed command: {command}")
            if command == "play_media":
                file_url = payload.get("media_content_id", "")
                if file_url.startswith("file://"):
                    file_path = file_url.replace("file://", "")
                    asyncio.run(play_audio(file_path))
            elif command in ["pause", "stop"]:
                current_state = "paused"
            elif command == "volume_set":
                volume = float(payload.get("value", volume))
            update_media_state()
    except json.JSONDecodeError as e:
        logging.error(f"❌ Invalid JSON received: {msg.payload.decode()} | Error: {e}")

# Setup MQTT client callbacks
client.on_connect = on_connect
client.on_message = on_message

# Connect to the broker and start the loop
client.connect(MQTT_BROKER, MQTT_PORT, 60)

def run_mqtt():
    try:
        while True:
            client.loop(timeout=1.0)
    except KeyboardInterrupt:
        logging.info("❌ Exiting MQTT...")
        client.disconnect()

mqtt_thread = threading.Thread(target=run_mqtt, daemon=True)
mqtt_thread.start()
