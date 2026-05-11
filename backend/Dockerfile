# =============================================================================
# Project Lumine — Backend Dockerfile
# Base: python:3.11-slim (minimal, no dev tools)
# Non-root user: lumine (reduces attack surface)
# Port: 8000
# =============================================================================

FROM python:3.11-slim

# System deps for pymysql + cryptography + pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps before copying source — layer cache stays valid
# when only code changes (not requirements)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# ---------------------------------------------------------------------------
# Non-root user — security hardening
# --disabled-password: no SSH login possible
# --no-create-home: no home directory (minimal filesystem footprint)
# ---------------------------------------------------------------------------
RUN adduser --disabled-password --no-create-home lumine \
 && chown -R lumine:lumine /app

USER lumine

EXPOSE 8000

# CMD is overridden by docker-compose to prepend `alembic upgrade head`
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
