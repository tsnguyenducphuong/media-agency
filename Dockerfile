FROM python:3.13-slim

RUN pip install --no-cache-dir uv==0.7.13

#For skia-python native libraries requirements
RUN apt-get update && apt-get install -y --no-install-recommends \
    libegl1 \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    libfontconfig1 \
    libgl1-mesa-glx \
    libgl1-mesa-dri \
    libgdk-pixbuf2.0-0 \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /app

COPY requirements.txt .
COPY . .  

# EXPOSE 8000
EXPOSE 8080

 
RUN pip install -r requirements.txt

#For Cloud Run
RUN adduser --disabled-password --gecos "" myuser && \
    chown -R myuser:myuser /app

ENV PATH="/home/myuser/.local/bin:$PATH"
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
#For Cloud Run

# CMD ["adk","web","--host","0.0.0.0","--port", "8000"] 
# CMD ["adk","web","--host","0.0.0.0","--port", "8080"] 

# TEST locally with Docker running following commands:
# docker build -t media_agent . 
# docker run -p 8000:8000 media_agent
# docker run -p 8080:8080 media_agent