FROM python:3.13.9-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy the requirements file into the container
COPY requirements.txt .

# 4. Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy our generator script into the container
COPY generator.py .

# 6. The command to run when the container starts
CMD ["python3", "generator.py"]