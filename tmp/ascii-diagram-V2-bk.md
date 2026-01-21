## Design
─
```text
┌───────────────────────┐        ┌───────────────────────────────────────────┐
│      IoT Devices      │        │                  Kafka                    │
│  sim-001: temp, hum   │  JSON  │  Topics:                                  │
│  sim-002: soil_moist  ├──────▶│   • iot.sensor.raw       (raw telemetry)   │
└───────────────────────┘        │   • iot.sensor.anomaly   (anomaly output) │
                                 └───────────────────────────────────────────┘
                                                │
                 ┌──────────────────────────────┼───────────────────────────────┐
                 │                              │                               │
                 │                              │                               │
                 ▼                              ▼                               ▼
┌──────────────────────────────┐   ┌────────────────────────────────────┐   ┌──────────────────────────────┐
│ Job 1: Archive (Streaming)   │   │ Job 2: Speed Layer (Streaming)     │   │   Arlert Consumers           │
│ Spark Structured Streaming    │  │ Spark Structured Streaming         │   │ e.g. alerting/ticketing      │
│                               │  │                                    │   │ from iot.sensor.anomaly      │
│ - Read: iot.sensor.raw        │  │ - Read: iot.sensor.raw             │   └──────────────────────────────┘
│ - Parse/validate schema       │  │ - Window features (mean/std/delta) │
│ - NO anomaly logic            │  │ - Anomaly detection (Z-score/EWMA) │
│ - Write raw → MinIO (Parquet) │  │ - Write:                           │
│   Partition by dt=YYYY-MM-DD  │  │    • Kafka iot.sensor.anomaly      │──────────.
└───────────────┬───────────────┘  │    • InfluxDB (metrics/anomalies)  │          │
                │                  │    • PostgreSQL (anomaly registry) │          │
                │                  └───────────────┬────────────────────┘          │
                │                                  │                               │
                ▼                                  ▼                               ▼
┌──────────────────────────────┐      ┌──────────────────────────┐   ┌──────────────────────────────┐
│   MinIO / S3 (Data Lake)      │     │   InfluxDB (Time-series) │   │  PostgreSQL (Relational)     │
│                               │     │                          │   │                              │
│ Zones:                        │     │ - sensor_metrics         │   │ - anomalies                  │
│  - raw/ (parquet, dt=...)     │     │ - sensor_anomalies       │   │ - devices metadata (opt)     │
│  - offline_stats/ (parquet)   │     └──────────────┬───────────┘   └──────────────┬───────────────┘
└───────────────┬──────────────┘                     │                              │
                │                                    │                              │
                ▼                                    └──────────────┬───────────────┘
┌───────────────────────────────┐                                   ▼
│ Job 3: Batch Layer (Offline)  │                     ┌───────────────────────────┐
│ Spark Batch                   │                     │          Grafana          │
│                               │                     │                           │
│ - Read MinIO raw/ by date     │                     │ Dashboards:               │
│ - Explode metrics             │                     │  - Realtime charts        │
│ - Compute mean/std/count      │                     │  - Anomaly score/flags    │
│ - (optional) thresholds       │                     │  - Top anomalies table    │
│ - Write offline_stats → MinIO │                     └───────────────────────────┘
└───────────────────────────────┘

```


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