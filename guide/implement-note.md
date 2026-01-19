# iot anamoly system

## Step 1: prepare python environment
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

```