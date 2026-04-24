FROM python:3.11-slim
RUN pip install --no-cache-dir mlflow psycopg2-binary boto3 gunicorn
WORKDIR /app
COPY start.sh /start.sh
RUN chmod +x /start.sh
EXPOSE 5000
CMD ["/start.sh"]