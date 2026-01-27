
-- =========================
-- Schema reset (order matters)
-- =========================
DROP TABLE IF EXISTS anomalies;
DROP TABLE IF EXISTS maintain_schedules;
DROP TABLE IF EXISTS devices;
DROP TABLE IF EXISTS zones;

-- =========================
-- Zones
-- =========================
CREATE TABLE IF NOT EXISTS zones (
    zone_id SERIAL PRIMARY KEY,
    zone_code TEXT UNIQUE NOT NULL,
    zone_name TEXT NOT NULL,
    protocol TEXT NOT NULL
);

-- =========================
-- Devices
-- =========================
CREATE TABLE IF NOT EXISTS devices (
    device_id TEXT PRIMARY KEY,
    zone_id INT NOT NULL REFERENCES zones(zone_id),
    model TEXT NOT NULL,
    sensor_type TEXT NOT NULL,
    metrics TEXT NOT NULL,
    base_values TEXT NOT NULL
);

-- =========================
-- Maintain Schedules
-- =========================
CREATE TABLE IF NOT EXISTS maintain_schedules (
    schedule_id SERIAL PRIMARY KEY,
    device_id TEXT NOT NULL REFERENCES devices(device_id),
    last_maintained DATE NOT NULL,
    next_maintained DATE NOT NULL,
    maint_type TEXT NOT NULL,
    notes TEXT
);

-- =========================
-- Anomalies
-- =========================
CREATE TABLE IF NOT EXISTS anomalies (
    id BIGSERIAL PRIMARY KEY,
    ts TIMESTAMPTZ NOT NULL,
    device_id TEXT NOT NULL REFERENCES devices(device_id),
    metric TEXT NOT NULL,
    value DOUBLE PRECISION,
    score DOUBLE PRECISION,
    method TEXT,
    severity TEXT
);

-- =========================
-- Seed data
-- =========================

-- Insert zones
INSERT INTO zones (zone_code, zone_name, protocol)
VALUES
('zone1', 'Production Floor', 'REST'),
('zone2', 'Storage Area', 'MQTT')
ON CONFLICT (zone_code) DO NOTHING;

-- Insert devices (Zone 1)
INSERT INTO devices (device_id, zone_id, model, sensor_type, metrics, base_values)
VALUES
('zone1-motor-001', (SELECT zone_id FROM zones WHERE zone_code='zone1'), 'Motor-A', 'Motor Monitoring',
 'motor_current_a, rpm, temperature_c', '6A, 1500 RPM, 60°C'),
('zone1-pump-001', (SELECT zone_id FROM zones WHERE zone_code='zone1'), 'Pump-B', 'Process Gauge',
 'pressure_bar, flow_lpm, temperature_c', '2 bar, 20 L/min, 55°C'),
('zone1-vibsensor-001', (SELECT zone_id FROM zones WHERE zone_code='zone1'), 'VibSense-X', 'Vibration Monitor',
 'accel_x_g, accel_y_g, accel_z_g, vibration_rms_g', '0.2g RMS'),
('zone1-acoustic-001', (SELECT zone_id FROM zones WHERE zone_code='zone1'), 'MicArray-Z', 'Acoustic Monitor',
 'sound_db', '70 dB')
ON CONFLICT (device_id) DO NOTHING;

-- Insert devices (Zone 2)
INSERT INTO devices (device_id, zone_id, model, sensor_type, metrics, base_values)
VALUES
('zone2-temp-001', (SELECT zone_id FROM zones WHERE zone_code='zone2'), 'ESP32-DHT22', 'Environment',
 'temperature, humidity', '24°C, 55%'),
('zone2-temp-002', (SELECT zone_id FROM zones WHERE zone_code='zone2'), 'ESP32-DHT22', 'Environment',
 'temperature, humidity', '22°C, 60%'),
('zone2-soil-001', (SELECT zone_id FROM zones WHERE zone_code='zone2'), 'ESP32-Soil', 'Soil Monitor',
 'soil_moisture, temperature', '35%, 23°C'),
('zone2-hvac-001', (SELECT zone_id FROM zones WHERE zone_code='zone2'), 'HVAC-Monitor', 'Climate Control',
 'temperature_c, pressure_bar, flow_lpm', '18°C, 1.5 bar, 15 L/min')
ON CONFLICT (device_id) DO NOTHING;

-- Insert maintenance schedules (fake dates)
INSERT INTO maintain_schedules (device_id, last_maintained, next_maintained, maint_type, notes)
VALUES
('zone1-motor-001', '2025-11-15', '2026-02-15', 'preventive', 'Bearing check, lubrication'),
('zone1-pump-001',  '2025-12-01', '2026-03-01', 'preventive', 'Seal inspection, pressure test'),
('zone1-vibsensor-001', '2025-10-20', '2026-01-20', 'calibration', 'Accelerometer calibration'),
('zone1-acoustic-001',  '2025-09-05', '2026-01-05', 'calibration', 'Mic sensitivity calibration'),
('zone2-temp-001', '2025-11-10', '2026-02-10', 'preventive', 'Sensor drift check'),
('zone2-temp-002', '2025-12-12', '2026-03-12', 'preventive', 'Filter replacement'),
('zone2-soil-001', '2025-08-25', '2026-02-25', 'preventive', 'Probe cleaning'),
('zone2-hvac-001', '2025-10-01', '2026-01-01', 'preventive', 'Valve and pressure check')
ON CONFLICT DO NOTHING;