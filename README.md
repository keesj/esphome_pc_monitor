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

## About AI

Following [unsloth](https://unsloth.ai/docs/models/qwen3.5)
Local LLM running on an NVIDIA spark + opencode + qwen 3.5

Design/Review & prompting keesj

## Design Decisions

### Single GPU Temperature Reader
All GPU temperature reads go through a single `read_gpu_temperatures()` function that returns an array of all GPU temperatures. This avoids multiple `nvidia-smi` calls per update cycle.

### Sensor Update Pattern
- `update_states()` is the only place that reads sensor data (every 5 seconds)
- Sensor classes no longer directly read hardware - they only provide data to the update loop
- This centralizes hardware access and simplifies testing

### GPU Sensor Naming
- 0 GPUs: No GPU sensor shown
- 1 GPU: Single "GPU Temperature" (no index suffix)
- 2-4 GPUs: Individual "GPU N Temperature" sensors
- 5+ GPUs: Individual sensors plus "GPU Statistics" with avg/max

### MAC Address Generation
MAC addresses are deterministically generated from the device name using MD5 hash. This ensures the same device always has the same MAC regardless of when it's started.

## License

MIT
