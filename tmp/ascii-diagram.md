## Design

```text
                           ┌───────────────────────────────┐
                           │           IoT Devices          │
                           │ temp / hum / vibration / ...   │
                           └───────────────┬───────────────┘
                                           │  JSON/Avro (key=device_id)
                                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                                   Kafka                                 │
│  Topics:                                                                │
│   • iot.sensor.raw       (raw telemetry)                                │
│   • iot.device.events    (downtime, errors, work orders - optional)     │
│   • iot.sensor.anomaly   (anomaly output)                               │
└───────────────┬───────────────────────────────┬─────────────────────────┘
                │                               │
                │ (stream consume)              │ (archive raw → data lake)
                │                               ▼
                │                   ┌───────────────────────────────┐
                │                   │    Object Storage (MinIO/S3)   │
                │                   │   Data Lake: raw/enriched      │
                │                   │   (JSON now, Parquet later)    │
                │                   └───────────────┬───────────────┘
                │                                   │
                │                                   ▼
                │                   ┌───────────────────────────────┐
                │                   │          Spark Batch           │
                │                   │ • offline analytics           │
                │                   │ • retrain model (optional)    │
                │                   │ • compute thresholds          │
                │                   └───────────────┬───────────────┘
                │                                   │ model params / reports
                │                                   ▼
                │                        (optional feedback to streaming)
                │
                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                 Spark Structured Streaming  (Speed Layer)                │
│  • Parse + validate schema                                               │
│  • Window features (mean/std/min/max/delta, etc.)                        │
│  • Anomaly inference: Z-score / EWMA / (optional IsolationForest)        │
│                                                                         │
│  Outputs:                                                               │
│   (1) anomalies → Kafka: iot.sensor.anomaly                              │
│   (2) raw & anomalies → InfluxDB (for charts/alerts)                     │
│   (3) anomalies → PostgreSQL (for join/report/audit)                     │
└───────────────┬───────────────────────────────┬─────────────────────────┘
                │                               │
                │ time-series write             │ relational write
                ▼                               ▼
┌───────────────────────────────┐     ┌──────────────────────────────────┐
│        InfluxDB (Time-series)  │     │       PostgreSQL (Relational)     │
│  • sensor_metrics  (raw)       │     │  • devices metadata               │
│  • sensor_anomalies            │     │    (device_id, location, model)   │
└───────────────┬───────────────┘     │  • maintenance schedule (optional) │
                │                     │  • ops events/logs (optional)      │
                │                     │  • anomalies registry              │
                │                     └───────────────┬───────────────────┘
                │                                     │ SQL queries / joins
                ▼                                     ▼
         ┌──────────────────────────────────────────────────────────┐
         │                         Grafana                          │
         │  • Time-series dashboards (InfluxDB)                      │
         │  • Alerts (threshold / anomaly count)                     │
         │  • Tables/Reports (PostgreSQL: top devices, by location)  │
         └──────────────────────────────────────────────────────────┘
```

```text
Thuyết minh 

1) Mục tiêu kiến trúc

Hệ thống nhằm phát hiện bất thường theo thời gian thực trên dữ liệu IoT (nhiệt độ, độ ẩm, rung, âm thanh, dòng điện motor…), đồng thời đảm bảo:
	•	Realtime processing (Speed layer) để phát hiện nhanh và cảnh báo
	•	Lưu trữ lịch sử (Data Lake) để phân tích offline / tái huấn luyện sau này
	•	Quan sát vận hành (Observability) qua dashboard + alert
	•	Truy vấn báo cáo (Reporting) dựa trên metadata và dữ liệu anomaly đã chuẩn hoá

2) Luồng dữ liệu realtime (Speed layer)
	1.	IoT Devices → Kafka

	•	Thiết bị gửi bản tin JSON/Avro lên topic iot.sensor.raw.
	•	Dùng device_id làm key để đảm bảo thứ tự và thuận lợi cho xử lý state/window theo từng thiết bị.

	2.	Kafka → Spark Structured Streaming
Spark Streaming đảm nhiệm:

	•	Parse & validate: loại bỏ bản tin lỗi schema/null
	•	Window feature extraction: tính toán theo cửa sổ (ví dụ 1 phút / 5 phút):
	    mean, std, min/max, delta, rate-of-change
	•	Anomaly inference:
	    Minimum: Z-score hoặc EWMA (unsupervised, dễ giải thích)
	    Tuỳ chọn nâng cao: IsolationForest

	3.	Output realtime

	•	InfluxDB: lưu sensor_metrics và sensor_anomalies để Grafana vẽ biểu đồ và đặt cảnh báo.
	•	PostgreSQL: lưu “anomalies registry” + join với devices metadata để làm báo cáo theo location/model và audit.
	•	Kafka iot.sensor.anomaly: publish kết quả để tích hợp về sau (notification service, ticketing, etc.).

⸻

3) Luồng dữ liệu batch (Data Lake / Batch layer)
	•	Kafka → Object Storage (MinIO/S3): archive raw events vào data lake.
	•	Spark Batch đọc dữ liệu lịch sử để:
	•	phân tích xu hướng theo ngày/tuần/tháng (offline analytics)
	•	(tuỳ chọn) retrain model/threshold
	•	xuất “model params / thresholds” để cập nhật cho speed layer (feedback loop)

Ở mức Minimum, bạn có thể chỉ cần “archive raw JSON theo partition ngày”, sau đó nâng lên Parquet nếu còn thời gian.

⸻

4) Vì sao cần cả InfluxDB và PostgreSQL?
	•	InfluxDB tối ưu cho time-series: vẽ chart realtime, downsample, alert theo thời gian.
	•	PostgreSQL tối ưu cho dữ liệu quan hệ: metadata (device/location/model), event logs (work orders), và truy vấn join/report:
	•	“Top 10 thiết bị có anomaly nhiều nhất 24h”
	•	“Anomaly theo location/model”
	•	“Anomaly trước/sau bảo trì” (nếu có maintenance events)

=> Tách đúng “time-series vs relational” làm đồ án trông rất chuẩn kiến trúc.
```