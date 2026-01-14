# ex01 — Ingestion and MinIO

This directory contains utilities to ingest data and push raw files or streaming batches to MinIO (S3-compatible). It also includes Terraform configuration to create the `raw-data` bucket locally.

Components
- `ingestion.py`: Kafka consumer that buffers click events and uploads them to MinIO using boto3. It currently listens to topic `clicks_topic`.
- `bucket_config.tf`: Terraform configuration to create the `raw-data` S3 bucket against local MinIO.

How it works
1. The consumer connects to Kafka and reads messages from `clicks_topic`.
2. Events are buffered and periodically written to MinIO as newline-delimited JSON files.
3. Static CSVs can be uploaded using the `upload_files_to_s3` helper.

Run notes
- If running inside Docker, set Kafka bootstrap to `kafka:29092`. If running on host, use `localhost:9092` and ensure the broker exposes that listener.
- Ensure MinIO is running and `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY` environment variables are correct.
- Create the bucket with Terraform (in `ex01`) or via MinIO UI.

Common issues & fixes
- Connection refused to Kafka: wrong bootstrap address for network context (container vs host). Use service name `kafka:29092` for containers.
- Credentials errors with boto3: ensure `endpoint_url` and keys are correct; use path-style access for MinIO.
- Large batches: tune `batch_size` and `max_interval` depending on throughput and memory.

Best practices
- Make uploads idempotent by using unique object keys (include timestamps or UUIDs).
- Include schema/version metadata with each uploaded file.
- Use TLS and authentication for production MinIO/Kafka.

See root `README.md` for overall architecture and streaming details.
