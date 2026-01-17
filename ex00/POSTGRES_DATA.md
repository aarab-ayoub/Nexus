# Clearing Postgres Data Between Restarts

## The Issue
When you do `docker-compose down` and `docker-compose up`, old data persists because Postgres data is stored in a volume (`./postgres_data`).

---

## Solutions

### Option 1: Clear Data on Restart (Recommended for Development)
```bash
# Stop containers
docker-compose down

# Remove the postgres data volume
rm -rf postgres_data

# Start fresh
docker-compose up -d
```

### Option 2: Clear Data Without Stopping Everything
```bash
# Stop only postgres
docker-compose stop postgres

# Remove data
rm -rf postgres_data

# Restart postgres
docker-compose up -d postgres
```

### Option 3: Use `docker-compose down -v` (Nuclear Option)
```bash
# Stop AND remove all volumes
docker-compose down -v

# This removes ALL data (postgres, logs, everything)
docker-compose up -d
```

---

## For Your Current Situation

Since you want fresh data:

```bash
cd /Users/ayoub/work/Nexus/ex00

# Stop containers
docker-compose down

# Clear postgres data
rm -rf postgres_data

# Restart everything
docker-compose up -d

# Recreate tables
docker exec -it postgres psql -U admin -d ecommerce -f /path/to/warehouse.sql
```

Or copy the SQL file into postgres and run it:
```bash
docker cp ../ex02/warehouse.sql postgres:/tmp/warehouse.sql
docker exec -it postgres psql -U admin -d ecommerce -f /tmp/warehouse.sql
```

---

## Why This Happens

Your `docker-compose.yml` has:
```yaml
postgres:
  volumes:
    - ./postgres_data:/var/lib/postgresql/data
```

This **persists** data across restarts. It's great for production, but for development you might want fresh data each time.

---

## Alternative: Use Named Volumes (Better)

Change your docker-compose.yml:
```yaml
postgres:
  volumes:
    - postgres_data:/var/lib/postgresql/data  # Named volume instead of bind mount

# At the bottom of docker-compose.yml
volumes:
  postgres_data:
```

Then use:
```bash
# Remove the named volume
docker-compose down -v

# Start fresh
docker-compose up -d
```

This is cleaner than manually deleting folders.
