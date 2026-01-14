# Nexus — ECommerce Data Engineering Project

## Project overview
This repository contains a small end-to-end data engineering exercise implementing batch and streaming ETL for a sample e‑commerce dataset. It demonstrates data generation, ingestion to object storage, and stream processing with Spark Structured Streaming writing aggregates to Postgres.

Folders:
- `ex00/` — Data generator, Kafka producer and local Docker environment (Kafka, Zookeeper, Postgres, MinIO, Spark images).
- `ex01/` — Ingestion utilities (consumer to capture events and upload to MinIO/S3 using boto3 + Terraform bucket config).
- `ex02/` — Batch + Stream ETL implemented with PySpark (reads CSV from S3A, streams from Kafka, writes to Postgres).

This README explains the architecture, key data engineering concepts, problems encountered in the exercise, the applied solutions, common pitfalls and best practices.

---

## Architecture (conceptual)

1. Data generation (ex00): a Python generator produces three CSV files (Users, Products, Orders) and a continuous stream of click events sent to Kafka.
2. Storage: static CSVs are uploaded to MinIO (S3-compatible) and can be read by Spark via the S3A connector.
3. Stream ingestion (ex01): a Kafka consumer illustrates streaming ingestion and can buffer messages and persist them to object storage.
4. Stream processing (ex02): Spark Structured Streaming consumes Kafka events, computes per-minute action counts (windowed aggregations), flattens results, and writes them to Postgres via JDBC.

---

## Data engineering concepts used
- Event-driven architecture: click events are modelled as JSON messages in Kafka topics.
- Batch ETL: periodic job that reads static CSV data, transforms and loads into a relational store (Postgres fact table).
- Stream ETL (micro-batch): Spark Structured Streaming runs continuous micro-batches to compute time-windowed metrics.
- Windowed aggregations: grouping events into time windows (tumbling windows) with watermarks to handle lateness.
- S3-compatible object storage (MinIO): used as the data lake for raw CSVs and archived click batches.
- Exactly-once / idempotency considerations: writing streaming aggregates to an RDBMS requires attention to semantics (append vs upsert) and deduplication.

---

## Problems found in the exercise and solutions (detailed)

1) Kafka connectivity from containers (Broker not reachable)
- Symptom: Spark logs show connection attempts to `localhost:9092` failing inside containers.
- Root cause: Docker container network — `localhost` inside a container is the container itself. The Kafka broker runs in its own container and advertises listeners differently for host vs internal network.
- Fix: Use internal advertised listener `kafka:29092` for container clients. Ensure `KAFKA_ADVERTISED_LISTENERS` in `docker-compose.yml` exposes both a host listener (e.g. `PLAINTEXT://localhost:9092`) and an internal listener (e.g. `PLAINTEXT_INTERNAL://kafka:29092`). Then configure containerized clients (Spark, generator, ingestion) to use `kafka:29092`.
- Tip: When debugging, inspect the broker container logs and ensure `KAFKA_ADVERTISED_LISTENERS` is correct for your deployment.

2) Topic name mismatch
- Symptom: Producer writes to `clicks_topic` but consumer/subscriber used `click_topic`.
- Fix: Standardize the topic name across all components. This exercise uses `clicks_topic`.

3) Writing Spark window struct to JDBC fails
- Symptom: Error like `Can't get JDBC type for struct<start:timestamp,end:timestamp>` when writing aggregated windowed results to Postgres.
- Root cause: Spark creates a `window` column of type struct(start, end). JDBC writer cannot map struct types to primitive DB types.
- Fix: Flatten the struct before writing, e.g.:
  - `page_views_flat = page_views.withColumn("window_start", F.col("window.start")).withColumn("window_end", F.col("window.end")).drop("window")`
  - Write `page_views_flat` to JDBC instead of the raw `page_views` DataFrame.

4) Timestamp parsing and schema
- Issue: If `timestamp` arrives as string, `from_json` yields string; converting with `F.to_timestamp` requires a compatible format.
- Fixes:
  - Declare the JSON schema with `TimestampType()` for `timestamp` when messages contain ISO timestamps, so `from_json` produces timestamp directly; or
  - Keep `StringType()` and call `F.to_timestamp("timestamp", format)` with the expected format.

5) Serialization issues using inline lambda in foreachBatch
- Symptom: Serialization/pickling errors when using inline lambda for `foreachBatch` in distributed mode.
- Fix: Use a top-level function `def write_batch(df, epoch_id): ...` and pass its name to `foreachBatch(write_batch)`.

6) Spark/Hadoop dependency and Guava conflicts
- Symptom: runtime errors referencing Guava methods when adding Hadoop/S3 or Kafka packages.
- Fix: Use tested package versions for the Spark cluster (example: `hadoop-aws:3.2.2` with Spark 3.3.0), or explicitly include a compatible Guava version. Add required packages on spark-submit with `--packages` or mount the correct jars.

---

## How the solution is implemented (short)
- Generator (`ex00/generator.py`) produces CSVs and streams click events to Kafka (`clicks_topic`) using the internal broker address `kafka:29092` inside Docker.
- Ingestion (`ex01/ingestion.py`) shows a Kafka consumer example and demonstrates uploading batches to MinIO (S3) using boto3.
- Stream ETL (`ex02/etl_job.py`) uses Spark Structured Streaming to:
  1. read from Kafka (`.format("kafka")`, `.option("kafka.bootstrap.servers","kafka:29092")`, `.option("subscribe","clicks_topic")`),
  2. parse JSON messages and ensure a timestamp column exists,
  3. compute per-minute counts grouped by action with watermarking,
  4. flatten the window struct (window_start, window_end),
  5. write results via `foreachBatch` into Postgres using JDBC.

---

## Common errors & how to avoid them
- Using `localhost` inside containers — prefer service hostnames (docker-compose service names) for inter-container communication.
- Forgetting to match topic names between producers and consumers.
- Writing complex types (struct, map, array) directly to JDBC — always flatten/convert to primitives.
- Relying on implicit timestamp parsing — define schemas or explicit formats.
- Not providing Kafka/S3 jars to Spark — include correct `--packages` on spark-submit.
- Not configuring checkpointing for streaming queries — add checkpoint path to guarantee recovery and at-least-once semantics.

---

## Operational notes and best practices
- Use checkpointing for structured streaming (`.option("checkpointLocation", "s3a://.../checkpoints/page_views")`) to support fault tolerance and exactly-once semantics when supported.
- For production writes to RDBMS, implement idempotent upserts (use staging tables + MERGE or write to a message queue consumed by a single writer).
- Monitor offsets and consumer groups with Kafka tools; avoid unbounded state in streaming jobs.
- Use well-defined schemas and evolve them carefully; store schema versions in metadata.

---

## How to run (local Docker)
1. Start docker-compose in `ex00/`:
   - `cd ex00 && docker-compose up -d zookeeper kafka postgres minio spark-masters spark-workers generator` (adjust services per local setup)
2. Build and run generator to create CSVs and stream events (generator container in `ex00`).
3. Ensure the `raw-data` bucket exists in MinIO (Terraform config in `ex01/` can create it).
4. Submit Spark job inside the spark-master container with required packages (see `ex02/note` for recommended spark-submit command and package list).

---

If you want, I can add SQL DDL statements for the Postgres tables, add checkpointing examples, or open a small ops guide with commands to reproduce the environment.  

---

License: educational exercise. 
