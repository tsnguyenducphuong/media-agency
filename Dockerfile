FROM python:3.12-slim

RUN pip install --no-cache-dir uv==0.7.13
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0


WORKDIR /app

COPY requirements.txt .
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     libfontconfig1 \
#     libgl1-mesa-glx \
#     libgl1-mesa-dri && \
#     pip install --no-cache-dir -r requirements.txt

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

RUN uv sync --frozen

EXPOSE 8080

# CMD ["uv", "run", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
CMD ["uv", "run", "."]