
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY model_server.py ./
COPY model.joblib ./
EXPOSE 8000
CMD ["uvicorn","model_server:app","--host","0.0.0.0","--port","8000"]
