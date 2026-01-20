# iot anamoly system

## Step 1: Create docker-compose.yml file

```shell
docker compose up -d
```

## Step 2: Configure MQTT Broker

Create mosquitto/config/mosquitto.conf

```shell
nano mosquitto/config/mosquitto.conf
```

```text
allow_anonymous false
password_file /mosquitto/config/password.txt
```

Create mosquitto/config/password.txt

```shell
nano mosquitto/config/password.txt
# create username and passworf 
# docker exec -it mosquitto mosquitto_passwd -b /mosquitto/config/password.txt <username> <password>
docker exec -it mosquitto mosquitto_passwd -b /mosquitto/config/password.txt iot P@sswordMQTT#2025
```

## Step 3

```text
# Recreate mosquitto with updated config (if changed)
docker compose -f iot-anomaly-system/docker-compose.yml up -d mosquitto

# Rebuild API to include paho-mqtt
docker compose -f iot-anomaly-system/docker-compose.yml build ingestion-api
docker compose -f iot-anomaly-system/docker-compose.yml up -d ingestion-api

docker exec -it mosquitto mosquitto_pub \
  -h mosquitto -p 1883 \
  -u iot -P 'P@sswordMQTT#2025' \
  -t 'iot/esp32-001/telemetry' \
  -m '{"device_id":"esp32-002","temperature":24.2,"humidity":52.1,"soil_moisture":31}'

  docker exec -it kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka:9092 \
  --topic iot.sensor.raw \
  --from-beginning \
  --property print.key=true --property print.value=true
```



## Step 99: prepare python environment
```shell
# sudo apt install -y python3-venv python3-pip
sudo apt install python3-full python3-venv

cd ./iot-anomaly-system
python3 -m venv .venv
source .venv/bin/activate

# install package in requirement
pip install -r requirements.txt

sudo sh -c 'echo "127.0.0.1 kafka" >> /etc/hosts'
grep kafka /etc/hosts
```

## Step 2: ingression-api

```shell
## Step 2.1 run for test
python ./ingression-api/main.py
# uvicorn ingestion-api.ingress-rest-api:app --host 0.0.0.0 --port 8000 --reload

## Step 2.2 run on docker with docker compose
docker compose up -d
```

```shell
curl http://localhost:6902/health

curl http://10.1.1.10:6902/health
curl https://api.technote.online/health

curl -X POST http://localhost:6902/ingest \
  -H "Content-Type: application/json" \
  -H "X-API-Key: team32-secret" \
  -d '{
    "device_id": "esp32-001",
    "location":"farm-zone-1",
    "model":"ESP32",
    "temperature": 28.2,
    "humidity": 65.0,
    "soil_moisture": 40.5
  }'

curl -X POST https://api.technote.online/ingest \
  -H "Content-Type: application/json" \
  -H "X-API-Key: team32-secret" \
  -d '{
    "device_id": "esp32-001",
    "location":"farm-zone-1",
    "model":"ESP32",
    "temperature": 28.2,
    "humidity": 65.0,
    "soil_moisture": 40.5
  }'
```