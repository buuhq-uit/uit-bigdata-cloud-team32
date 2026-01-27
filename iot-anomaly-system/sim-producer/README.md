# IoT Sensor Simulator - Multi-Zone Multi-Protocol

Hệ thống giả lập các cảm biến IoT thời gian thực với phân vùng theo zone và giao thức truyền thông.

## 📋 Device Registry

### **Zone 1 - Production Floor (REST API)**
| Device ID | Model | Sensor Type | Metrics | Base Values |
|-----------|-------|-------------|---------|-------------|
| `zone1-motor-001` | Motor-A | Motor Monitoring | `motor_current_a`, `rpm`, `temperature_c` | 6A, 1500 RPM, 60°C |
| `zone1-pump-001` | Pump-B | Process Gauge | `pressure_bar`, `flow_lpm`, `temperature_c` | 2 bar, 20 L/min, 55°C |
| `zone1-vibsensor-001` | VibSense-X | Vibration Monitor | `accel_x_g`, `accel_y_g`, `accel_z_g`, `vibration_rms_g` | 0.2g RMS |
| `zone1-acoustic-001` | MicArray-Z | Acoustic Monitor | `sound_db` | 70 dB |

### **Zone 2 - Storage Area (MQTT)**
| Device ID | Model | Sensor Type | Metrics | Base Values |
|-----------|-------|-------------|---------|-------------|
| `zone2-temp-001` | ESP32-DHT22 | Environment | `temperature`, `humidity` | 24°C, 55% |
| `zone2-temp-002` | ESP32-DHT22 | Environment | `temperature`, `humidity` | 22°C, 60% |
| `zone2-soil-001` | ESP32-Soil | Soil Monitor | `soil_moisture`, `temperature` | 35%, 23°C |
| `zone2-hvac-001` | HVAC-Monitor | Climate Control | `temperature_c`, `pressure_bar`, `flow_lpm` | 18°C, 1.5 bar, 15 L/min |

## 🏗️ Architecture

```text
sim-producer/
├── main.py              # Entry point with zone-based config
├── config.py            # Device registry & zone definitions
├── generators/          # Sensor signal generators
│   ├── __init__.py
│   ├── base.py         # Base generator class
│   ├── vibration.py    # Vibration/accelerometer
│   ├── acoustic.py     # Sound/microphone
│   ├── motor.py        # Motor current + RPM
│   ├── process.py      # Temperature, pressure, flow
│   └── environment.py  # Temp, humidity, soil
├── transports/          # Communication protocols
│   ├── __init__.py
│   ├── rest_client.py
│   └── mqtt_client.py
└── README.md           # Documentation
```

## 🚀 Usage


```bash
# Run Both Zones (Default)
python3 main.py --mode both --interval 1.0

# Run Zone 1 Only (REST API)
python3 main.py --mode zone1 \
  --api-url http://localhost:6902 \
  --api-key team32-secret \
  --interval 1.0

# Run Zone 2 Only (MQTT)
python3 main.py --mode zone2 \
  --mqtt-host localhost \
  --mqtt-port 1883 \
  --mqtt-username iot \
  --mqtt-password 'P@sswordMQTT#2025' \
  --mqtt-base-topic iot \
  --interval 1.0

#   Faster Sampling (0.5s interval)
python3 main.py --mode both --interval 0.5
```

## Signal Characteristics
### Vibration Signals
- 3-axis accelerometer (X, Y, Z) với multi-frequency simulation
- RMS vibration tính toán từ 3 trục
- Anomaly injection: Random spikes (1% probability, 4x magnitude)

### Acoustic Signals
Sound level (dB) với slow oscillation
Anomaly injection: Sudden loud spikes (2% probability)

### Motor Monitoring
- Current (A): Slow drift với load variations
- RPM: Very slow oscillation
- Temperature: Follows current draw
- Anomaly injection: Overload (1.8x current), RPM drop (0.6x), overheat (1.25x temp)

### Process Gauges
- Temperature, Pressure, Flow: Correlated slow cycles
- Anomaly injection: Independent spikes on each metric

### Environment Sensors
- Temperature & Humidity: Slow random walk
- Soil Moisture: Bounded [0, 100]%

## Adding New Devices
### 1. Define device in config.py:

```python
DeviceConfig(
    device_id="zone1-newdevice-001",
    model="NewModel-X",
    location="zone1-production-floor",
    sensor_type="custom_sensor",
    generator_class="CustomGenerator",
    generator_params={"param1": 10.0}
)
```
### 2. Create generator in generators/:

```python
class CustomGenerator(BaseGenerator):
    def __init__(self, ctx: DeviceContext, param1: float = 10.0):
        super().__init__(ctx)
        self.param1 = param1
    
    def next_metrics(self) -> Dict[str, float]:
        return {"metric_name": value}
```

### 3. Register in main.py:
```python
GENERATOR_MAP["CustomGenerator"] = CustomGenerator
```

## 📦 Dependencies
```bash
pip install requests paho-mqtt
```

## 🎯 Integration
- REST → Ingestion API → Kafka topic iot.sensor.raw
- MQTT → Mosquitto → MQTT Bridge → Kafka topic iot.sensor.raw
- Spark Streaming reads from Kafka and processes all metrics automatically
- InfluxDB stores time-series data
- Grafana visualizes metrics and anomalies

