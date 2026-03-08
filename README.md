# ESPHome PC Monitor

A PC temperature monitoring system that exposes CPU and GPU temperatures as ESPHome sensors via API and web interface.

## Features

- Reads CPU temperature from Linux thermal zones
- Reads GPU temperature using nvidia-smi (supports multiple GPUs)
- Individual sensors for each GPU
- Statistics (avg/max) when more than 4 GPUs are present
- Web interface for monitoring
- ESPHome API integration

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python esphome_pc_monitor.py [OPTIONS]
```

### Options

- `--name NAME`: Device name (default: hostname)
- `--api-port PORT`: ESPHome API port (default: 6053)
- `--web-port PORT`: Web interface port (default: 8083)

### Examples

```bash
# Use default hostname as device name
python esphome_pc_monitor.py

# Custom device name and ports
python esphome_pc_monitor.py --name my-pc --api-port 6053 --web-port 8083
```

## Hardware Requirements

- Linux system with thermal sensors
- NVIDIA GPU(s) with nvidia-smi available

## How It Works

- CPU temperature is read from `/sys/class/thermal/thermal_zone0/temp` or `/sys/class/hwmon/hwmon0/temp1_input`
- GPU temperatures are read using `nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader`
- Sensors are updated every 5 seconds
- MAC address is deterministically generated from device name using MD5 hash

##

Generator opencode + qwen3.5

## License

MIT
