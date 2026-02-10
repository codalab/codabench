web: cd src && gunicorn asgi:application -w 3 -k uvicorn.workers.UvicornWorker -b :$PORT --max-requests 1024 --max-requests-jitter 256
worker: cd src && celery -A celery_config worker -B -Q site-worker -l info -n site-worker@%n --concurrency=3
