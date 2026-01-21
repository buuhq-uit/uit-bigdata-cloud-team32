FROM apache/spark:3.5.1

USER root

# Base tools and Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip ca-certificates curl procps \
 && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1
ENV SPARK_HOME=/opt/spark
WORKDIR /opt/spark-app

# Copy app files (jobs + runner)
COPY . /opt/spark-app

# Python deps needed by the jobs
RUN pip3 install --no-cache-dir \
    requests \
    influxdb-client \
    pandas \
    numpy \
    psycopg2-binary

# Ensure runner is executable
# RUN chmod +x /opt/spark-app/start_all_jobs.sh

# Postgres JDBC driver available to Spark
# If you have a specific version jar, keep its name; otherwise postgresql.jar
# The repo already contains /opt/spark-app/postgresql.jar
RUN cp /opt/spark-app/postgresql.jar /opt/spark/jars/postgresql.jar

# Pre-create ivy dir used by the script (optional but helpful)
RUN mkdir -p /opt/spark-app/.ivy2

# Default command starts the three jobs via the runner
# CMD ["bash", "/opt/spark-app/start_all_jobs.sh"]
