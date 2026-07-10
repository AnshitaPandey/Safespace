FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# torch CPU wheel keeps the image smaller than the default CUDA build; fine for this workload.
RUN pip install --no-cache-dir -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

COPY . .

# Model checkpoints (once trained) get mounted or COPYed into /app/checkpoints
RUN mkdir -p /app/checkpoints

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8100"]
