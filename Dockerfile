FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
# 容器内自动注入环境变量，指向宿主机
ENV LM_STUDIO_BASE=http://host.docker.internal:1234

WORKDIR /app

RUN pip install --no-cache-dir \
    flask \
    flask-cors \
    requests \
    duckduckgo-search \
    ddgs

COPY . .
EXPOSE 5000
CMD ["python", "app.py"]