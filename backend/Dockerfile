FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY migrations ./migrations
COPY tests ./tests
COPY pytest.ini ./pytest.ini
COPY docker-entrypoint.sh ./docker-entrypoint.sh
RUN chmod +x ./docker-entrypoint.sh
EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
# A website-chat request blocks (I/O-wait) on the webchat-bridge model turn for up
# to WEBCHAT_TIMEOUT (~75s). With plain sync workers a couple of slow chats would
# starve every other request, and the default 30s worker timeout would kill them.
# gthread keeps fast page/API requests responsive alongside slow, I/O-bound chats.
CMD ["gunicorn", "app.main:create_app()", "--bind", "0.0.0.0:8000", \
     "--worker-class", "gthread", "--workers", "2", "--threads", "8", \
     "--timeout", "120", "--graceful-timeout", "30"]
