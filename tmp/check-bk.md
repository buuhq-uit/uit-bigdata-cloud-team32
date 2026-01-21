## Check script

```shell
sudo sh -c 'echo "127.0.0.1 kafka" >> /etc/hosts'
grep kafka /etc/hosts

sudo sh -c 'echo "127.0.0.1 kafka" >> /etc/hosts'
grep kafka /etc/hosts

source .venv/bin/activate

```

check kafka consume:

```shell
docker exec -it kafka sh -lc '
/opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka:9092 \
  --topic iot.sensor.raw \
  --from-beginning \
  --max-messages 5
'
```

```shell
chmod +x run_spark_streaming.sh
./run_spark_streaming.sh

```

### anomoly produce test
```shell
docker exec -it kafka sh -lc '
for i in $(seq 1 20); do
  ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  if [ $i -le 10 ]; then
    echo "{\"ts\":\"$ts\",\"device_id\":\"dev-02\",\"temperature\":25.$i,\"humidity\":55.$i}"
  else
    echo "{\"ts\":\"$ts\",\"device_id\":\"dev-02\",\"temperature\":120.0,\"humidity\":5.0}"
  fi
done | /opt/kafka/bin/kafka-console-producer.sh --bootstrap-server kafka:9092 --topic iot.sensor.raw
'

docker exec -it kafka sh -lc '
echo "{\"ts\":\"2026-01-13T00:00:00Z\",\"device_id\":\"sim-001\",\"metrics\":{\"temperature\":42.5,\"humidity\":70.0}}" \
| /opt/kafka/bin/kafka-console-producer.sh --bootstrap-server kafka:9092 --topic iot.sensor.raw
'
```

```text
from(bucket: "iot-bucket")
  |> range(start: -15m)
  |> filter(fn: (r) => r._measurement == "sensor_metrics")
```

```text
from(bucket: "iot-bucket")
  |> range(start: -15m)
  |> filter(fn: (r) => r._measurement == "sensor_metrics")
  |> filter(fn: (r) => r._field == "value")
  |> filter(fn: (r) => r.metric =~ /temperature|humidity|soil_moisture/)

```