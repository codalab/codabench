web: cd src && gunicorn asgi:application -w 4 -k uvicorn.workers.UvicornWorker -b :$PORT --max-requests 1024 --max-requests-jitter 256
worker: cd src && celery -A celery_config worker -B -Q site-worker -Ofast -Ofair -l info -n site-worker@%n --without-gossip --without-mingle --without-heartbeat --concurrency=3
