#web: cd src && waitress-serve --port=$PORT wsgi:application
web: cd src && gunicorn wsgi:application -k gevent -b :$PORT -b :80
