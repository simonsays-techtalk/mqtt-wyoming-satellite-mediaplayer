# mqtt-wyoming-satellite-mediaplayer
This code allows mediaplayer integration for wyoming satellite, based on mqtt.

# Wyoming Satellite Installation and Setup Guide

## 🚀 Overview
This guide details all the steps required to **install, configure, and run Wyoming Satellite** on a Raspberry Pi. It includes **fixes for audio issues, MQTT media player integration, and Home Assistant setup**.

---
## ✅ **1. System Preparation**

### **1.1 Update the System**
```bash
sudo apt update && sudo apt upgrade -y
```

### **1.2 Create the `satellite` User (if not already created)**
```bash
sudo adduser --gecos "" --disabled-password satellite
sudo usermod -aG sudo satellite
```
Switch to the user:
```bash
sudo su - satellite
```

---
## ✅ **2. Install Required Packages**
```bash
sudo apt install -y python3 python3-venv python3-pip git mpg123 mosquitto-clients
```

---
## ✅ **3. Set Up the Virtual Environment**
```bash
python3 -m venv ~/.wyoming_env
source ~/.wyoming_env/bin/activate
pip install --upgrade pip
pip install paho-mqtt asyncio numpy wave
```

---
## ✅ **4. Clone and Install Wyoming Satellite**
```bash
git clone https://github.com/rhasspy/wyoming-satellite.git ~/wyoming-satellite
cd ~/wyoming-satellite
pip install .
```

---
## ✅ **5. Configure ALSA for the Seeed 2-Mic Voicecard (MS)**
### **5.1 Disable Unnecessary Audio Devices**
Edit `config.txt`:
```bash
sudo nano /boot/firmware/config.txt
```
Add the following line:
```ini
dtoverlay=vc4-kms-v3d,noaudio
```
Save and exit, then reboot:
```bash
sudo reboot
```

### **5.2 Verify and Configure ALSA**
```bash
arecord -l && aplay -l
```
Check if `MS` (seeed-2-mic-voicecard) is listed, or any other audiodevice.

**Create or edit ALSA configuration:**
```bash
sudo nano /etc/asound.conf
```
Paste:
```ini
defaults.pcm.card MS
defaults.ctl.card MS
```
Save and restart ALSA:
```bash
sudo systemctl restart alsa-restore
```
Reboot:
```bash
sudo reboot
```

Test audio:
```bash
aplay -D plughw:CARD=MS,DEV=0 /usr/share/sounds/alsa/Front_Center.wav
```

---
## ✅ **6. Set Up Wyoming Satellite as a Systemd Service**
Create the service file:
```bash
sudo tee /etc/systemd/system/wyoming-satellite.service > /dev/null <<EOF
[Unit]
Description=Wyoming Satellite Service
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
ExecStart=/home/satellite/wyoming-satellite/script/run --name 'satellite-mqtt' \
  --uri 'tcp://0.0.0.0:10700' \
  --mic-command 'arecord -D plughw:CARD=MS,DEV=0 -r 16000 -c 1 -f S16_LE -t raw' \
  --snd-command 'aplay -D plughw:CARD=MS,DEV=0 -r 22050 -c 1 -f S16_LE -t raw'
WorkingDirectory=/home/satellite/wyoming-satellite
Restart=always
RestartSec=1

[Install]
WantedBy=default.target
EOF
```
Reload systemd:
```bash
sudo systemctl daemon-reload
sudo systemctl enable wyoming-satellite
sudo systemctl start wyoming-satellite
```
Check status:
```bash
systemctl status wyoming-satellite
```

---
## ✅ **7. MQTT Testing**
Test MQTT connection:
```bash
mosquitto_pub -h YOURIPADDRESS -u USER -P PASSWORD -t "test/topic" -m "Hello from Wyoming Satellite"
mosquitto_sub -h YOURIPADDRESS -u USER -P PASSWORD -t "test/topic"
```

---
## ✅ **8. Test Media Playback via MQTT**
Play a `.wav` file:
```bash
mosquitto_pub -h YOURIPADDRESS -u USER -P PASSWORD -t "homeassistant/media_player/wyoming_satellite/command" \
  -m '{"command": "play_media", "media_content_id": "file:///home/satellite/wyoming-satellite/sounds/awake.wav"}'
```
Check logs for playback:
```bash
journalctl -u wyoming-satellite --no-pager --lines=50
```

---
## ✅ **9. Test TTS via MQTT**
```bash
mosquitto_pub -h YOURIPADDRESS -u USER -P PASSWORD -t "homeassistant/tts/speak" \
  -m '{"entity_id": "tts.piper", "message": "Hello from Wyoming Satellite"}'
```

---
## 🎯 **Final Confirmation Checklist**
✅ **Microphone and speaker work** (`arecord` and `aplay` tests)  
✅ **Wyoming Satellite starts on boot** (`systemctl status wyoming-satellite`)  
✅ **MQTT works (`mosquitto_pub` test)**  
✅ **Media playback via MQTT works (`play_media` command)**  
✅ **TTS works via MQTT (`tts.speak` command)**  
✅ **Home Assistant detects Wyoming Satellite as a media player**  

---
### 🎉 **Wyoming Satellite is now fully operational!** 🚀

