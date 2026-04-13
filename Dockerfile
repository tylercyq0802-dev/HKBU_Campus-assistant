# ---------------------------------------------------
# Stage One: Kitchen (Builder Stage)
# Task: Prepare the environment and install all Python dependencies
# ---------------------------------------------------
# We choose the Debian-based Python 3.11 slim version, which is lightweight and highly compatible
FROM python:3.11-slim AS builder

# Set the working directory, which is equivalent to us carving out a workspace called /app in the container
WORKDIR /app

# [Optimization points] After confirmation, requirements.txt uses precompiled packages such as psycopg2-binary (pre-made ingredients),
# so we have completely removed heavy system compilation tools like gcc, making the build speed take off!
# Bring the dependency list into the 'kitchen'
COPY requirements.txt .

# Install the dependency packages into a dedicated directory (--user mode), making it convenient to move the entire setup in the next stage
# --no-cache-dir can prevent cache from taking up space
RUN pip install --user --no-cache-dir -r requirements.txt


# ---------------------------------------------------
# Stage Two: Dining Table / Bento Box (Production Stage)
# Task: Only bring the necessary code and packed packages, travel light
# ---------------------------------------------------
FROM python:3.11-slim

WORKDIR /app

# [Key Point] Directly copy the prepared "dishes" (installed third-party dependency packages) from the "kitchen" (builder stage)
COPY --from=builder /root/.local /root/.local

# Put our core business code into the container
# Note: we don't need to copy files like venv, .env, etc. We will exclude them later using .dockerignore
COPY ChatGPT_HKBU.py config(cleaned).ini db.py main.py ./

# Tell the system where to find the third-party package that was just installed
ENV PATH=/root/.local/bin:$PATH

# Set the timezone to Hong Kong time (optional, friendly for scheduled tasks)
ENV TZ=Asia/Hong_Kong

# Startup command automatically executed after the container is powered on
CMD ["python", "main.py"]
