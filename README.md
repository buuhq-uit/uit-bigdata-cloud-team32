# Phân tích dữ liệu lớn và điện toán đám mây 
# IS6108.CH191
```text
Thư mục tài liệu: https://drive.google.com/drive/folders/1pjz9nTF1saEh2Q9HiPVO3FZ4k1YcKxAJ?usp=drive_link

File excel Đăng ký đồ án: https://docs.google.com/spreadsheets/d/1tRC64g3e5HXS8ZQKc0Uisq0zvFWrFPhl/edit?usp=drive_link&ouid=106738876590867505745&rtpof=true&sd=true

```

```text
https://github.com/Miceuz/docker-compose-mosquitto-influxdb-telegraf-grafana


```

# Nhóm 32

```text
Huỳnh Quốc Bữu
Trần Võ Bảo Thiên 240104052
```

# Tên đề tài

```text
Phát hiện bất thường trong dữ liệu IoT (nhiệt độ, độ ẩm, cảm biến môi trường) bằng Spark Streaming và Kafka
```

## Comment của Thầy Bình

```text
Dữ liệu cần thu thập:

- Tín hiệu cảm biến thời gian thực: vibration (accelerometer), acoustic (microphone), motor current, RPM, temperature, pressure, flow…
- Metadata: thiết bị ID, vị trí, model, lịch bảo trì, lịch vận hành (on/off), tải máy.
- Sự kiện vận hành / log: lỗi, thay phụ tùng, downtime, work orders.
- Nhãn (nếu có): thời điểm xảy ra lỗi, loại lỗi (dùng cho supervised / semi-supervised)

Time-series DB: InfluxDB / TimescaleDB cho dữ liệu cảm biến.
HDFS / S3 / Object storage cho lưu batch/large.
Meta/relational: PostgreSQL.

Speed layer: Flink / Spark Streaming (real-time feature extraction + inference).
Batch layer: Spark (huấn luyện, re-train, offline analytics).
```

```text
Grafana: http://localhost:3000
 (admin/admin)

InfluxDB: http://localhost:8086
 (admin/admin12345)

MinIO Console: http://localhost:9001
 (minioadmin/minioadmin123)
```

```text
- PPT -> Slide thuyết trình
        + Trang Bìa (Tên topic, nhóm thực hiện)
        + Mục lục
        + Gioi thiệu
        + .....
        + Kết luận và hướng phát triển
        + Tham khảo
- PDF -> Báo cáo (Xúc tích, không quá 15 trang)
- Link Video Demo (Nếu có), github (Nếu có) hoặc bất kỳ tham khảo nào phải đặt trong Page tham khảo của PPT.
```


