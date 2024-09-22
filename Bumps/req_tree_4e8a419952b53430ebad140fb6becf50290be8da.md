```bash
aiofiles 0.4.0 File support for asyncio.
argh 0.26.2 An unobtrusive argparse wrapper with natural syntax
azure-storage-blob 2.1.0 Microsoft Azure Storage Blob Client Library for Python
├── azure-common >=1.1.5
└── azure-storage-common >=2.1,<3.0
    ├── azure-common >=1.1.5 
    ├── cryptography * 
    │   └── cffi >=1.12 
    │       └── pycparser * 
    ├── python-dateutil * 
    │   └── six >=1.5 
    └── requests * 
        ├── certifi >=2017.4.17 
        ├── charset-normalizer >=2,<4 
        ├── idna >=2.5,<4 
        └── urllib3 >=1.21.1,<3 
azure-storage-common 2.1.0 Microsoft Azure Storage Common Client Library for Python
├── azure-common >=1.1.5
├── cryptography *
│   └── cffi >=1.12 
│       └── pycparser * 
├── python-dateutil *
│   └── six >=1.5 
└── requests *
    ├── certifi >=2017.4.17 
    ├── charset-normalizer >=2,<4 
    ├── idna >=2.5,<4 
    └── urllib3 >=1.21.1,<3 
bleach 3.1.4 An easy safelist-based HTML-sanitizing tool.
├── six >=1.9.0
└── webencodings *
blessings 1.7 A thin, practical wrapper around terminal coloring, styling, and positioning
└── six *
boto3 1.9.68 The AWS SDK for Python
├── botocore >=1.12.68,<1.13.0
│   ├── docutils >=0.10,<0.16 
│   ├── jmespath >=0.7.1,<1.0.0 
│   ├── python-dateutil >=2.1,<3.0.0 
│   │   └── six >=1.5 
│   └── urllib3 >=1.20,<1.26 
├── jmespath >=0.7.1,<1.0.0
└── s3transfer >=0.1.10,<0.2.0
    └── botocore >=1.3.0,<2.0.0 
        ├── docutils >=0.10,<0.16 
        ├── jmespath >=0.7.1,<1.0.0 
        ├── python-dateutil >=2.1,<3.0.0 
        │   └── six >=1.5 
        └── urllib3 >=1.20,<1.26 
bpython 0.21 Fancy Interface to the Python Interpreter
├── curtsies >=0.3.5
│   ├── blessed >=1.5 
│   │   ├── jinxed >=1.1.0 
│   │   │   └── ansicon * 
│   │   ├── six >=1.9.0 
│   │   └── wcwidth >=0.1.4 
│   └── cwcwidth * 
├── cwcwidth *
├── greenlet *
├── pygments *
├── pyxdg *
└── requests *
    ├── certifi >=2017.4.17 
    ├── charset-normalizer >=2,<4 
    ├── idna >=2.5,<4 
    └── urllib3 >=1.21.1,<3 
celery 4.2.1 Distributed Task Queue.
├── billiard >=3.5.0.2,<3.6.0
├── kombu >=4.2.0,<5.0
│   └── amqp >=2.6.0,<2.7 
│       └── vine >=1.1.3,<5.0.0a1 
└── pytz >0.0-dev
channels 2.4.0 Brings async, event-driven capabilities to Django. Django 2.2 and up only.
├── asgiref >=3.2,<4.0
│   └── typing-extensions >=4 
├── daphne >=2.3,<3.0
│   ├── asgiref >=3.2,<4.0 
│   │   └── typing-extensions >=4 
│   ├── autobahn >=0.18 
│   │   ├── cryptography >=3.4.6 
│   │   │   └── cffi >=1.12 
│   │   │       └── pycparser * 
│   │   ├── hyperlink >=21.0.0 
│   │   │   └── idna >=2.5 
│   │   ├── setuptools * 
│   │   └── txaio >=21.2.1 
│   └── twisted >=18.7 
│       ├── attrs >=19.2.0 
│       ├── automat >=0.3.0 
│       │   └── typing-extensions * (circular dependency aborted here)
│       ├── constantly >=15.1 
│       ├── hyperlink >=17.1.1 (circular dependency aborted here)
│       ├── idna >=0.6,<2.3 || >2.3 (circular dependency aborted here)
│       ├── incremental >=16.10.1 
│       │   ├── setuptools >=61.0 (circular dependency aborted here)
│       │   └── tomli * 
│       ├── pyhamcrest >=1.9.0,<1.10.0 || >1.10.0 
│       ├── pyopenssl >=16.0.0 
│       │   └── cryptography >=41.0.5,<44 (circular dependency aborted here)
│       ├── service-identity >=18.1.0 
│       │   ├── attrs >=19.1.0 (circular dependency aborted here)
│       │   ├── cryptography * (circular dependency aborted here)
│       │   ├── pyasn1 * 
│       │   └── pyasn1-modules * 
│       │       └── pyasn1 >=0.4.6,<0.7.0 (circular dependency aborted here)
│       └── zope-interface >=4.4.2 
│           └── setuptools * (circular dependency aborted here)
└── django >=2.2
    ├── pytz * 
    └── sqlparse >=0.2.2 
channels-redis 3.2.0 Redis-backed ASGI channel layer implementation
├── aioredis >=1.0,<2.0
│   ├── async-timeout * 
│   └── hiredis * 
├── asgiref >=3.2.10,<4
│   └── typing-extensions >=4 
├── channels <4
│   ├── asgiref >=3.2,<4.0 
│   │   └── typing-extensions >=4 
│   ├── daphne >=2.3,<3.0 
│   │   ├── asgiref >=3.2,<4.0 (circular dependency aborted here)
│   │   ├── autobahn >=0.18 
│   │   │   ├── cryptography >=3.4.6 
│   │   │   │   └── cffi >=1.12 
│   │   │   │       └── pycparser * 
│   │   │   ├── hyperlink >=21.0.0 
│   │   │   │   └── idna >=2.5 
│   │   │   ├── setuptools * 
│   │   │   └── txaio >=21.2.1 
│   │   └── twisted >=18.7 
│   │       ├── attrs >=19.2.0 
│   │       ├── automat >=0.3.0 
│   │       │   └── typing-extensions * (circular dependency aborted here)
│   │       ├── constantly >=15.1 
│   │       ├── hyperlink >=17.1.1 (circular dependency aborted here)
│   │       ├── idna >=0.6,<2.3 || >2.3 (circular dependency aborted here)
│   │       ├── incremental >=16.10.1 
│   │       │   ├── setuptools >=61.0 (circular dependency aborted here)
│   │       │   └── tomli * 
│   │       ├── pyhamcrest >=1.9.0,<1.10.0 || >1.10.0 
│   │       ├── pyopenssl >=16.0.0 
│   │       │   └── cryptography >=41.0.5,<44 (circular dependency aborted here)
│   │       ├── service-identity >=18.1.0 
│   │       │   ├── attrs >=19.1.0 (circular dependency aborted here)
│   │       │   ├── cryptography * (circular dependency aborted here)
│   │       │   ├── pyasn1 * 
│   │       │   └── pyasn1-modules * 
│   │       │       └── pyasn1 >=0.4.6,<0.7.0 (circular dependency aborted here)
│   │       └── zope-interface >=4.4.2 
│   │           └── setuptools * (circular dependency aborted here)
│   └── django >=2.2 
│       ├── pytz * 
│       └── sqlparse >=0.2.2 
└── msgpack >=1.0,<2.0
coreapi 2.3.3 Python client library for Core API.
├── coreschema *
│   └── jinja2 * 
│       └── markupsafe >=2.0 
├── itypes *
├── requests *
│   ├── certifi >=2017.4.17 
│   ├── charset-normalizer >=2,<4 
│   ├── idna >=2.5,<4 
│   └── urllib3 >=1.21.1,<3 
└── uritemplate *
dj-database-url 0.4.2 Use Database URLs in your Django Application.
django 2.2.17 A high-level Python Web framework that encourages rapid development and clean, pragmatic design.
├── pytz *
└── sqlparse >=0.2.2
django-ajax-selects 2.0.0 Edit ForeignKey, ManyToManyField and CharField in Django Admin using jQuery UI AutoComplete.
django-cors-middleware 1.5.0 django-cors-middleware is a Django application for handling the server headers required for Cross-Origin Resource Sharing (CORS). Fork of django-cors-headers.
django-debug-toolbar 3.2 A configurable set of panels that display various debug information about the current request/response.
├── django >=2.2
│   ├── pytz * 
│   └── sqlparse >=0.2.2 
└── sqlparse >=0.2.0
django-enforce-host 1.0.1 Middleware to redirect requests to a canonical hostname
django-extensions 2.2.6 Extensions for Django
└── six >=1.2
django-extra-fields 0.9 Additional fields for Django Rest Framework.
django-filter 2.4.0 Django-filter is a reusable Django application for allowing users to filter querysets dynamically.
└── django >=2.2
    ├── pytz * 
    └── sqlparse >=0.2.2 
django-oauth-toolkit 1.0.0 OAuth2 Provider for Django
├── django >=1.10
│   ├── pytz * 
│   └── sqlparse >=0.2.2 
├── oauthlib >=2.0.1
└── requests >=2.13.0
    ├── certifi >=2017.4.17 
    ├── charset-normalizer >=2,<4 
    ├── idna >=2.5,<4 
    └── urllib3 >=1.21.1,<3 
django-querycount 0.7.0 Middleware that Prints the number of DB queries to the runserver console.
django-redis 4.12.1 Full featured redis cache backend for Django.
├── django >=2.2
│   ├── pytz * 
│   └── sqlparse >=0.2.2 
└── redis >=3.0.0
django-redis-cache 3.0.0 Redis Cache Backend for Django
└── redis <4.0
django-storages 1.7.2 Support for many storage backends in Django
├── azure-storage-blob >=1.3.1
│   ├── azure-common >=1.1.5 
│   └── azure-storage-common >=2.1,<3.0 
│       ├── azure-common >=1.1.5 (circular dependency aborted here)
│       ├── cryptography * 
│       │   └── cffi >=1.12 
│       │       └── pycparser * 
│       ├── python-dateutil * 
│       │   └── six >=1.5 
│       └── requests * 
│           ├── certifi >=2017.4.17 
│           ├── charset-normalizer >=2,<4 
│           ├── idna >=2.5,<4 
│           └── urllib3 >=1.21.1,<3 
├── django >=1.11
│   ├── pytz * 
│   └── sqlparse >=0.2.2 
└── google-cloud-storage >=0.22.0
    ├── google-api-core >=2.15.0,<3.0.0dev 
    │   ├── google-auth >=2.14.1,<3.0.dev0 
    │   │   ├── cachetools >=2.0.0,<6.0 
    │   │   ├── pyasn1-modules >=0.2.1 
    │   │   │   └── pyasn1 >=0.4.6,<0.7.0 
    │   │   └── rsa >=3.1.4,<5 
    │   │       └── pyasn1 >=0.1.3 (circular dependency aborted here)
    │   ├── googleapis-common-protos >=1.56.2,<2.0.dev0 
    │   │   └── protobuf >=3.20.2,<4.21.1 || >4.21.1,<4.21.2 || >4.21.2,<4.21.3 || >4.21.3,<4.21.4 || >4.21.4,<4.21.5 || >4.21.5,<6.0.0.dev0 
    │   ├── proto-plus >=1.22.3,<2.0.0dev 
    │   │   └── protobuf >=3.19.0,<6.0.0dev (circular dependency aborted here)
    │   ├── protobuf >=3.19.5,<3.20.0 || >3.20.0,<3.20.1 || >3.20.1,<4.21.0 || >4.21.0,<4.21.1 || >4.21.1,<4.21.2 || >4.21.2,<4.21.3 || >4.21.3,<4.21.4 || >4.21.4,<4.21.5 || >4.21.5,<6.0.0.dev0 (circular dependency aborted here)
    │   └── requests >=2.18.0,<3.0.0.dev0 
    │       ├── certifi >=2017.4.17 
    │       ├── charset-normalizer >=2,<4 
    │       ├── idna >=2.5,<4 
    │       └── urllib3 >=1.21.1,<3 
    ├── google-auth >=2.26.1,<3.0dev (circular dependency aborted here)
    ├── google-cloud-core >=2.3.0,<3.0dev 
    │   ├── google-api-core >=1.31.6,<2.0.dev0 || >2.3.0,<3.0.0dev (circular dependency aborted here)
    │   └── google-auth >=1.25.0,<3.0dev (circular dependency aborted here)
    ├── google-crc32c >=1.0,<2.0dev 
    ├── google-resumable-media >=2.7.2 
    │   └── google-crc32c >=1.0,<2.0dev (circular dependency aborted here)
    └── requests >=2.18.0,<3.0.0dev (circular dependency aborted here)
django-su 0.9.0 Login as any user from the Django admin interface, then switch back when done
└── django >=1.11
    ├── pytz * 
    └── sqlparse >=0.2.2 
djangorestframework 3.9.1 Web APIs for Django, made easy.
djangorestframework-csv 2.1.0 CSV Tools for Django REST Framework
├── djangorestframework *
├── six *
└── unicodecsv *
drf-extensions 0.4.0 Extensions for Django REST Framework
└── djangorestframework >=3.8.1
drf-writable-nested 0.5.4 Writable nested helpers for django-rest-framework's serializers
drf-yasg 1.11.0 Automated generation of real Swagger/OpenAPI 2.0 schemas from Django Rest Framework code.
├── coreapi >=2.3.3
│   ├── coreschema * 
│   │   └── jinja2 * 
│   │       └── markupsafe >=2.0 
│   ├── itypes * 
│   ├── requests * 
│   │   ├── certifi >=2017.4.17 
│   │   ├── charset-normalizer >=2,<4 
│   │   ├── idna >=2.5,<4 
│   │   └── urllib3 >=1.21.1,<3 
│   └── uritemplate * 
├── coreschema >=0.0.4
│   └── jinja2 * 
│       └── markupsafe >=2.0 
├── django >=1.11.7
│   ├── pytz * 
│   └── sqlparse >=0.2.2 
├── djangorestframework >=3.7.7
├── flex >=6.11.1
│   ├── click >=3.3 
│   ├── jsonpointer >=1.7 
│   ├── pyyaml >=3.11 
│   ├── requests >=2.4.3 
│   │   ├── certifi >=2017.4.17 
│   │   ├── charset-normalizer >=2,<4 
│   │   ├── idna >=2.5,<4 
│   │   └── urllib3 >=1.21.1,<3 
│   ├── rfc3987 >=1.3.4 
│   ├── six >=1.7.3 
│   ├── strict-rfc3339 >=0.7 
│   └── validate-email >=1.2 
├── inflection >=0.3.1
├── ruamel-yaml >=0.15.34
│   └── ruamel-yaml-clib >=0.2.7 
├── six >=1.10.0
├── swagger-spec-validator >=2.1.0
│   ├── importlib-resources >=1.3 
│   │   └── zipp >=3.1.0 
│   ├── jsonschema * 
│   │   ├── attrs >=22.2.0 
│   │   ├── jsonschema-specifications >=2023.03.6 
│   │   │   └── referencing >=0.31.0 
│   │   │       ├── attrs >=22.2.0 (circular dependency aborted here)
│   │   │       └── rpds-py >=0.7.0 
│   │   ├── referencing >=0.28.4 (circular dependency aborted here)
│   │   └── rpds-py >=0.7.1 (circular dependency aborted here)
│   ├── pyyaml * 
│   └── typing-extensions * 
└── uritemplate >=3.0.0
factory-boy 2.11.1 A versatile test fixtures replacement based on thoughtbot's factory_bot for Ruby.
└── faker >=0.7.0
    └── python-dateutil >=2.4 
        └── six >=1.5 
flake8 3.8.4 the modular source code checker: pep8 pyflakes and co
├── mccabe >=0.6.0,<0.7.0
├── pycodestyle >=2.6.0a1,<2.7.0
└── pyflakes >=2.2.0,<2.3.0
flex 6.12.0 Swagger Schema validation.
├── click >=3.3
├── jsonpointer >=1.7
├── pyyaml >=3.11
├── requests >=2.4.3
│   ├── certifi >=2017.4.17 
│   ├── charset-normalizer >=2,<4 
│   ├── idna >=2.5,<4 
│   └── urllib3 >=1.21.1,<3 
├── rfc3987 >=1.3.4
├── six >=1.7.3
├── strict-rfc3339 >=0.7
└── validate-email >=1.2
gunicorn 20.0.4 WSGI HTTP Server for UNIX
└── setuptools >=3.0
ipdb 0.13.0 IPython-enabled pdb
├── ipython >=5.1.0
│   ├── appnope * 
│   ├── backcall * 
│   ├── black * 
│   │   ├── click >=7.1.2 
│   │   ├── mypy-extensions >=0.4.3 
│   │   ├── pathspec >=0.9.0,<1 
│   │   ├── platformdirs >=2 
│   │   ├── tomli >=0.2.6,<2.0.0 
│   │   └── typing-extensions >=3.10.0.0 
│   ├── colorama * 
│   ├── decorator * 
│   ├── jedi >=0.16 
│   │   └── parso >=0.8.3,<0.9.0 
│   ├── matplotlib-inline * 
│   │   └── traitlets * 
│   ├── pexpect >4.3 
│   │   └── ptyprocess >=0.5 
│   ├── pickleshare * 
│   ├── prompt-toolkit >=2.0.0,<3.0.0 || >3.0.0,<3.0.1 || >3.0.1,<3.1.0 
│   │   └── wcwidth * 
│   ├── pygments * 
│   ├── setuptools >=18.5 
│   ├── stack-data * 
│   │   ├── asttokens >=2.1.0 
│   │   │   └── six >=1.12.0 
│   │   ├── executing >=1.2.0 
│   │   └── pure-eval * 
│   └── traitlets >=5 (circular dependency aborted here)
└── setuptools *
jinja2 3.1.4 A very fast and expressive template engine.
└── markupsafe >=2.0
markdown 2.6.11 Python implementation of Markdown.
oyaml 0.7 Ordered YAML: drop-in replacement for PyYAML which preserves dict ordering
└── pyyaml *
pillow 10.3.0 Python Imaging Library (Fork)
psycopg2-binary 2.8.6 psycopg2 - Python-PostgreSQL Database Adapter
pygments 2.2.0 Pygments is a syntax highlighting package written in Python.
pyrabbit2 1.0.7 A Pythonic interface to the RabbitMQ Management HTTP API
└── requests *
    ├── certifi >=2017.4.17 
    ├── charset-normalizer >=2,<4 
    ├── idna >=2.5,<4 
    └── urllib3 >=1.21.1,<3 
pytest 6.2.1 pytest: simple powerful testing with Python
├── atomicwrites >=1.0
├── attrs >=19.2.0
├── colorama *
├── iniconfig *
├── packaging *
├── pluggy >=0.12,<1.0.0a1
├── py >=1.8.2
└── toml *
pytest-django 4.1.0 A Django plugin for pytest.
└── pytest >=5.4.0
    ├── atomicwrites >=1.0 
    ├── attrs >=19.2.0 
    ├── colorama * 
    ├── iniconfig * 
    ├── packaging * 
    ├── pluggy >=0.12,<1.0.0a1 
    ├── py >=1.8.2 
    └── toml * 
pytest-pythonpath 0.7.3 pytest plugin for adding to the PYTHONPATH from command line or configs.
└── pytest >=2.5.2
    ├── atomicwrites >=1.0 
    ├── attrs >=19.2.0 
    ├── colorama * 
    ├── iniconfig * 
    ├── packaging * 
    ├── pluggy >=0.12,<1.0.0a1 
    ├── py >=1.8.2 
    └── toml * 
python-dateutil 2.7.3 Extensions to the standard Python datetime module
└── six >=1.5
pyyaml 5.3.1 YAML parser and emitter for Python
selenium 3.141.0 Python bindings for Selenium
└── urllib3 *
six 1.16.0 Python 2 and 3 compatibility utilities
social-auth-app-django 3.1.0 Python Social Authentication, Django integration.
├── six *
└── social-auth-core >=1.2.0
    ├── defusedxml >=0.5.0rc1 
    ├── oauthlib >=1.0.3 
    ├── pyjwt >=1.4.0 
    ├── python3-openid >=3.0.10 
    │   └── defusedxml * (circular dependency aborted here)
    ├── requests >=2.9.1 
    │   ├── certifi >=2017.4.17 
    │   ├── charset-normalizer >=2,<4 
    │   ├── idna >=2.5,<4 
    │   └── urllib3 >=1.21.1,<3 
    ├── requests-oauthlib >=0.6.1 
    │   ├── oauthlib >=3.0.0 (circular dependency aborted here)
    │   └── requests >=2.0.0 (circular dependency aborted here)
    └── six >=1.10.0 
social-auth-core 2.0.0 Python social authentication made simple.
├── defusedxml >=0.5.0rc1
├── oauthlib >=1.0.3
├── pyjwt >=1.4.0
├── python3-openid >=3.0.10
│   └── defusedxml * 
├── requests >=2.9.1
│   ├── certifi >=2017.4.17 
│   ├── charset-normalizer >=2,<4 
│   ├── idna >=2.5,<4 
│   └── urllib3 >=1.21.1,<3 
├── requests-oauthlib >=0.6.1
│   ├── oauthlib >=3.0.0 
│   └── requests >=2.0.0 
│       ├── certifi >=2017.4.17 
│       ├── charset-normalizer >=2,<4 
│       ├── idna >=2.5,<4 
│       └── urllib3 >=1.21.1,<3 
└── six >=1.10.0
twisted 20.3.0 An asynchronous networking framework written in Python
├── attrs >=19.2.0
├── automat >=0.3.0
│   └── typing-extensions * 
├── constantly >=15.1
├── hyperlink >=17.1.1
│   └── idna >=2.5 
├── idna >=0.6,<2.3 || >2.3
├── incremental >=16.10.1
│   ├── setuptools >=61.0 
│   └── tomli * 
├── pyhamcrest >=1.9.0,<1.10.0 || >1.10.0
├── pyopenssl >=16.0.0
│   └── cryptography >=41.0.5,<44 
│       └── cffi >=1.12 
│           └── pycparser * 
├── service-identity >=18.1.0
│   ├── attrs >=19.1.0 
│   ├── cryptography * 
│   │   └── cffi >=1.12 
│   │       └── pycparser * 
│   ├── pyasn1 * 
│   └── pyasn1-modules * 
│       └── pyasn1 >=0.4.6,<0.7.0 (circular dependency aborted here)
└── zope-interface >=4.4.2
    └── setuptools * 
urllib3 1.24.3 HTTP library with thread-safe connection pooling, file post, and more.
uvicorn 0.13.3 The lightning-fast ASGI server.
├── click ==7.*
├── colorama >=0.4
├── h11 >=0.8
├── httptools ==0.1.*
├── python-dotenv >=0.13
├── pyyaml >=5.1
├── uvloop >=0.14.0
├── watchgod >=0.6,<0.7
└── websockets ==8.*
watchdog 2.1.1 Filesystem events monitoring
websockets 8.1 An implementation of the WebSocket Protocol (RFC 6455 & 7692)
whitenoise 5.2.0 Radically simplified static file serving for WSGI applications
```
