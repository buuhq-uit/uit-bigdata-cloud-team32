
# demo scenario

## System Design

## System Design to docker-compose

## System Design to repository & docker-compose

### Repository: 
https://github.com/buuhq-uit/uit-bigdata-cloud-team32

### Modules:
- ./esp32-board: hardware code (sensors)
- ./iot-anomaly-system/anomoly-alert: demo alert (throw log) when anomaly appear
- ./iot-anomaly-system/grafana: 

## Demo:

### Step 1: Start docker services
- script:
```bash
docker compose up -d
```
- expect: 09 containers running

### Step 2: Run 3 Spark Jobs on spark-jobs container
- script:
```shell
./run_job1_archive.sh
./run_job2_speed.sh
./run_job3_batch.sh
```
- expect: 3 processes running
```shell
## check process
docker exec -it spark-jobs bash -lc "ps aux | grep -F 'job1_archive_to_minio.py' | grep -v grep"
docker exec -it spark-jobs bash -lc "ps aux | grep -F 'job2_speed_anomaly_to_influx.py' | grep -v grep"
docker exec -it spark-jobs bash -lc "ps aux | grep -F 'job3_batch_offline_analytics.py' | grep -v grep"
```

### Step 3: Start sim-producer to send fake data (sensors)
- script:
```shell
# source .venv/bin/activate
#sudo sh -c 'echo "127.0.0.1 kafka" >> /etc/hosts'
# grep kafka /etc/hosts
python sim-producer/main.py
```
- expect:
```shell
## log sending in console ok
## log on ingestion-api container ok
## consume on kafka ok
docker exec -it kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka:9092 \
  --topic iot.sensor.raw \
  --from-beginning \
  --property print.key=true --property print.value=true
```

### Step 4: check raw data on MinIO
- script: http://localhost:6901
 (minioadmin/minioadmin123)
- expect: thấy data

### Step 5: Check data on influxdb
 - script: http://localhost:8086 (admin/admin12345)
 ```shell
 from(bucket: "iot-bucket")
  |> range(start: -15m)
  |> filter(fn: (r) => r._measurement == "sensor_metrics")
 ```

 - expect: thấy data

### Step 6: Check data anomaly
- script:
```sql
-- on postgres db
delete from anomalies;
select * from anomalies;
-- check log on anomaly-alert container
```
- expect: thấy data

### Step 7: Grafana dashboards
- script: http://localhost:3000
 (admin/admin)
 - expect: dashboard work