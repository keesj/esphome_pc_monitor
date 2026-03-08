import argparse
import asyncio
import hashlib
import logging
import os
import socket

from aioesphomeserver import Device, SensorEntity

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def generate_mac_from_name(name: str) -> str:
    md5_hash = hashlib.md5(name.encode()).digest()
    mac_bytes = [0x02, 0x00, 0x00] + list(md5_hash[:9])
    mac_bytes[1] = (mac_bytes[1] & 0xFE) | 0x02
    return ":".join(f"{b:02x}" for b in mac_bytes[:6])


async def read_gpu_temperatures():
    try:
        process = await asyncio.create_subprocess_exec(
            "nvidia-smi",
            "--query-gpu=temperature.gpu",
            "--format=csv,noheader",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if stdout:
            temps = [
                float(t.strip())
                for t in stdout.decode().strip().split("\n")
                if t.strip()
            ]
            return temps
        if stderr:
            logger.debug(f"nvidia-smi stderr: {stderr.decode().strip()}")
    except Exception as e:
        logger.debug(f"Failed to read GPU temps: {e}")
    return []


class TemperatureSensor(SensorEntity):
    def __init__(self, name, object_id, sensor_type, gpu_index=None):
        super().__init__(
            name=name,
            object_id=object_id,
            unit_of_measurement="°C",
            accuracy_decimals=1,
            device_class="temperature",
        )
        self.sensor_type = sensor_type
        self.gpu_index = gpu_index

    async def read_temperature(self):
        if self.sensor_type == "cpu":
            return await self.read_cpu_temperature()
        return 0.0

    async def read_cpu_temperature(self):
        for path in [
            "/sys/class/thermal/thermal_zone0/temp",
            "/sys/class/hwmon/hwmon0/temp1_input",
        ]:
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        return float(f.read().strip()) / 1000.0
                except Exception as e:
                    logger.debug(f"Failed to read CPU temp from {path}: {e}")
        return 0.0


async def main():
    parser = argparse.ArgumentParser(description="PC Temperature Monitor")
    parser.add_argument(
        "--name",
        default=socket.gethostname(),
        help="Device name (default: hostname)",
    )
    parser.add_argument(
        "--api-port",
        type=int,
        default=6053,
        help="ESPHome API port (default: 6053)",
    )
    parser.add_argument(
        "--web-port",
        type=int,
        default=8083,
        help="Web interface port (default: 8083)",
    )

    args = parser.parse_args()

    mac_address = generate_mac_from_name(args.name)
    logger.info(f"Device name: {args.name}")
    logger.info(f"Generated MAC: {mac_address}")

    device = Device(name=args.name, mac_address=mac_address)

    cpu_sensor = TemperatureSensor(
        name="CPU Temperature",
        object_id="cpu_temperature",
        sensor_type="cpu",
    )
    device.add_entity(cpu_sensor)

    gpus = await get_gpu_count()
    logger.info(f"Detected {gpus} GPU(s)")

    gpu_sensors = []
    stats_sensor = None
    if gpus > 0:
        if gpus == 1:
            gpu_sensor = TemperatureSensor(
                name="GPU Temperature",
                object_id="gpu_temperature",
                sensor_type="gpu",
                gpu_index=0,
            )
            device.add_entity(gpu_sensor)
            gpu_sensors.append(gpu_sensor)
        else:
            for i in range(gpus):
                gpu_sensor = TemperatureSensor(
                    name=f"GPU {i} Temperature",
                    object_id=f"gpu_{i}_temperature",
                    sensor_type="gpu",
                    gpu_index=i,
                )
                device.add_entity(gpu_sensor)
                gpu_sensors.append(gpu_sensor)

            if gpus > 4:
                stats_sensor = TemperatureSensor(
                    name="GPU Statistics",
                    object_id="gpu_statistics",
                    sensor_type="gpu_stats",
                )
                device.add_entity(stats_sensor)

    async def update_states():
        while True:
            try:
                cpu_temp = await cpu_sensor.read_temperature()
                await cpu_sensor.set_state(cpu_temp)

                if gpus > 0:
                    all_temps = await read_gpu_temperatures()
                    if all_temps:
                        for i, sensor in enumerate(gpu_sensors):
                            if i < len(all_temps):
                                await sensor.set_state(all_temps[i])

                        if gpus > 4 and stats_sensor is not None:
                            avg_temp = sum(all_temps) / len(all_temps)
                            max_temp = max(all_temps)
                            stats = f"Avg: {avg_temp:.1f}°C, Max: {max_temp:.1f}°C"
                            await stats_sensor.set_state(avg_temp)
                            logger.info(f"GPU Stats: {stats}")

                        gpu_temps = [round(t, 1) for t in all_temps]
                        logger.info(f"CPU: {cpu_temp}°C, GPU(s): {gpu_temps}")

            except Exception as e:
                logger.error(f"Error updating sensor state: {e}")

            await asyncio.sleep(5)

    logger.info("Starting device...")

    await asyncio.gather(
        device.run(api_port=args.api_port, web_port=args.web_port),
        update_states(),
    )


async def get_gpu_count():
    temps = await read_gpu_temperatures()
    return len(temps)


if __name__ == "__main__":
    asyncio.run(main())
