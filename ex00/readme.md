# ROUBLESHOOTING GUIDE - Spark + Docker Setup

## ⚠️ Known Issues & Solutions

This document contains solutions to common problems when setting up Spark with Docker for the Data Engineering Module.

---

## Issue #1: Guava Version Conflict

### Symptoms:
```
java.lang.NoSuchMethodError: com.google.common.base.Preconditions.checkArgument
```

### Root Cause:
Spark 3.3.0 and Hadoop 3.3.0+ have incompatible Guava library versions.

###  Solution:
**Use Hadoop 3.2.2 instead of 3.3.0:**
```bash
docker exec -it spark-master /spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --packages org.apache.hadoop:hadoop-aws:3.2.2,org.postgresql:postgresql:42.2.23 \
  /app/etl_job.py
```

**Alternative:** Add explicit Guava version:
```bash
--packages org.apache.hadoop:hadoop-aws:3.2.2,org.postgresql:postgresql:42.2.23,com.google.guava:guava:23.0
```

---

##  Issue #2: Spark Worker Not Starting

### Symptoms:
```
java.lang.IllegalArgumentException: requirement failed: startPort should be between 1024 and 65535
```
- Job stuck in `WAITING` state
- No workers visible in Spark UI (http://localhost:8080)

### Root Cause:
BDE2020 Spark worker image requires explicit port configuration.

### Solution:
Add these environment variables to your worker service in `docker-compose.yml`:
```yaml
spark-worker-1:
  image: bde2020/spark-worker:3.3.0-hadoop3.3
  environment:
    - "SPARK_MASTER=spark://spark-master:7077"
    - "SPARK_WORKER_CORES=2"
    - "SPARK_WORKER_MEMORY=2g"
    - "SPARK_WORKER_PORT=8881"       # ← ADD THIS
    - "SPARK_WORKER_WEBUI_PORT=8081" # ← ADD THIS
```

---

##  Issue #3: Python F-String Syntax Error

### Symptoms:
```python
SyntaxError: invalid syntax
    base_s3_path = f"s3a://raw-data/{date}"
                                           ^
```

### Root Cause:
Older Python versions (< 3.6) in some Spark Docker images don't support f-strings.

###  Solution:
Use `.format()` instead:
```python
#  Don't use:
base_s3_path = f"s3a://raw-data/{processing_date_str}"

#  Use instead:
base_s3_path = "s3a://raw-data/{0}".format(processing_date_str)
```
---

##  Recommended Docker Image Versions

### What Works (Tested):
```yaml
# Spark Cluster
spark-master: bde2020/spark-master:3.3.0-hadoop3.3
spark-worker: bde2020/spark-worker:3.3.0-hadoop3.3

# Dependencies
zookeeper: confluentinc/cp-zookeeper:7.0.1
kafka: confluentinc/cp-kafka:7.0.1
postgres: postgres:13
minio: minio/minio:latest
```

###  What to Avoid:
- ❌ Bitnami Spark images (now paid/restricted)
- ❌ Mixing Spark 3.3.0 with Hadoop 3.3.0+ (Guava conflicts)
- ❌ Using `gettyimages/spark` (outdated, unsupported)
- ❌ Spark 2.x images (too old for modern S3A)
