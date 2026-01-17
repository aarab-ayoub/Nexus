# Security Best Practices for Nexus Project

## ⚠️ CRITICAL: Never commit secrets to git!

This project uses **environment variables** for secure credential management.

---

## Current Setup: Environment Variables via .env File

### ✅ What We're Doing Right
- Credentials are stored in `.env` file (git-ignored)
- `docker-compose.yml` references them with `${VARIABLE_NAME}` syntax
- Python code reads them using `os.getenv()` - NO hardcoded values
- `.gitignore` protects the `.env` file
- `.env.example` template helps new team members

### 🔐 Where Credentials Live
- **Development**: `.env` file in `ex00/` directory (git-ignored)
- **Docker Compose**: Uses `${VAR}` syntax to read from `.env`
- **Containers**: Receive env vars from docker-compose
- **Python**: Reads via `os.getenv()`

---

## How It Works

### 1. Setting Credentials (.env file)
```bash
# ex00/.env (git-ignored)
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=your_database
SNOWFLAKE_SCHEMA=your_schema
```

### 2. Referencing in docker-compose.yml (safe to commit)
```yaml
spark-masters:
  environment:
    - SNOWFLAKE_USER=${SNOWFLAKE_USER}
    - SNOWFLAKE_PASSWORD=${SNOWFLAKE_PASSWORD}
    # Docker Compose reads these from .env automatically
```

### 3. Reading Credentials (Python)
```python
import os

USER = os.getenv("SNOWFLAKE_USER")  # No defaults, no hardcoding
PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")

# Validate they exist
if not all([USER, PASSWORD, ...]):
    raise ValueError("Missing credentials!")
```

---

## 🚨 IMPORTANT: Before Committing to Git

### DO:
✅ Use `.env` file for credentials (git-ignored)  
✅ Use `${VARIABLE}` syntax in docker-compose.yml  
✅ Commit `.env.example` as a template  
✅ Keep `.env` in `.gitignore`  
✅ Use validation (`if not all([...])`) to catch missing vars early  
✅ Document required env vars in `.env.example`

### DON'T:
❌ Hardcode credentials in Python files  
❌ Hardcode credentials in docker-compose.yml  
❌ Commit `.env` files  
❌ Use default values in `os.getenv("VAR", "default_secret")`  
❌ Share your actual credentials in documentation

---

## Production Recommendations

For production deployments, use **secret management services**:

1. **AWS Secrets Manager** / **Azure Key Vault** / **GCP Secret Manager**
   - Best for cloud deployments
   - Automatic rotation, audit logging
   
2. **Kubernetes Secrets**
   - If deploying on K8s
   - Use with RBAC for access control

3. **HashiCorp Vault**
   - Enterprise-grade secret management
   - Works with any infrastructure

4. **Docker Swarm/Kubernetes Sealed Secrets**
   - Encrypted secrets in version control

---

## Required Environment Variables

### Snowflake
- `SNOWFLAKE_USER` - Snowflake username
- `SNOWFLAKE_PASSWORD` - Snowflake password
- `SNOWFLAKE_ACCOUNT` - Account identifier (e.g., `abc12345.us-east-1`)
- `SNOWFLAKE_WAREHOUSE` - Warehouse name
- `SNOWFLAKE_DATABASE` - Database name
- `SNOWFLAKE_SCHEMA` - Schema name

### PostgreSQL (currently hardcoded, consider moving to env vars)
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`

### MinIO
- `MINIO_ROOT_USER`
- `MINIO_ROOT_PASSWORD`

---

## Quick Start for New Team Members

1. Copy the template: `cp .env.example .env`
2. Edit `.env` with your actual credentials
3. **NEVER** commit `.env` to git (it's in `.gitignore`)
4. Run `docker-compose up -d`

### How Docker Compose Reads .env

Docker Compose **automatically** loads `.env` from the same directory:

```bash
ex00/
├── .env              # Your secrets (git-ignored)
├── .env.example      # Template (safe to commit)
├── docker-compose.yml # Uses ${VAR} syntax (safe to commit)
```

When you run `docker-compose up`, it:
1. Reads `.env` file
2. Substitutes `${SNOWFLAKE_USER}` → actual value
3. Passes env vars to containers

---

## Troubleshooting

### Error: "Missing required Snowflake environment variables"
**Cause**: `.env` file missing or variables not set  
**Fix**: 
1. Check if `.env` exists in `ex00/` directory
2. Copy from template: `cp .env.example .env`
3. Fill in your actual credentials
4. Restart: `docker-compose down && docker-compose up -d`

### Error: Variables showing as `${SNOWFLAKE_USER}` literally
**Cause**: `.env` file not in the same directory as `docker-compose.yml`  
**Fix**: Ensure `.env` is in `ex00/` directory, not `ex02/`

### Verify env vars are loaded
```bash
# Check if docker-compose reads them
docker-compose config | grep SNOWFLAKE

# Check inside container
docker exec -it spark-master env | grep SNOWFLAKE
```

---

## Why This Approach?

| Method | Security | Simplicity | Production-Ready |
|--------|----------|------------|------------------|
| Hardcoded | ❌ NEVER | ✅ | ❌ |
| .env + dotenv | ⚠️ Risky | ✅ | ⚠️ |
| Docker env vars | ✅ Good | ✅ | ✅ |
| Secret managers | ✅ Best | ⚠️ | ✅ |

**Our choice**: Docker env vars - Best balance for this project's scale.

---

Last updated: 2026-01-17
