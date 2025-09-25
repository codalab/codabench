Compared to Codalab, installing Codabench should be relatively easy since you no longer have to worry about special ways to set up SSL or storage. We include default solutions that should handle that for most basic uses.

## Pre-requisites

### Install Docker and Docker Compose
- [Docker](https://docs.docker.com/install/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Clone Repository
Download the Codabench repository:

```bash
git clone https://github.com/codalab/codabench
```

## Edit the settings (.env)

The `.env` file contains the settings of your instance.
On a fresh installation, you will need to use the following command to get your `.env` file: 

```bash
cd codabench
cp .env_sample .env
```

Then edit the necessary settings inside. The most important are the database, storage, and Caddy/SSL settings. For a quick **local** setup, you should not need to edit this file. For a [public server deployment](How-to-deploy-Codabench-on-your-server.md), you will have to modify some settings.

!!! warning "It is important to change the default passwords if you intend for the instance to be public"

If you are using `AWS_S3_ENDPOINT_URL=http://minio:9000/` in your `.env`, edit your `/etc/hosts` file by adding this line `127.0.0.1 minio`


#### For MacOS

In `.env`, replace:
```ini
AWS_S3_ENDPOINT_URL=http://minio:9000/
```

by

```ini
AWS_S3_ENDPOINT_URL=http://docker.for.mac.localhost:9000/
```
!!! note "If needed, some troubleshooting of this step is provided at [the end of this page](#troubleshooting-storage-endpoint-url) or [in this page](How-to-deploy-Codabench-on-your-server.md#frequently-asked-questions-faqs)"

## Start the service

To deploy the platform, run:

```bash
docker compose up -d
``` 

## Run the following commands

Create the required tables in the database:

```bash
docker compose exec django ./manage.py migrate
```

Generate the required static resource files:

```bash
docker compose exec django ./manage.py collectstatic --noinput
```  

You should be able to verify it is running correctly by looking at the logs with `docker compose logs -f` and by visiting `localhost:80` (Depending on your configuration).


## Advanced Configuration

### Testing

To run automated tests for your local instance, get inside the Django container with `docker compose exec django bash` then run `py.test` to start the automated tests.


### SSL
To enable SSL:

- If you already have a DNS for your server that is appropriate, in the `.env` simply set `DOMAIN_NAME` to your DNS. Remove any port designation like `:80`. This will have Caddy serve both HTTP and HTTPS.

!!! warning "For a public instance, HTTPS is strongly recomended"

### Validate user account on local instance

When deploying a local instance, the email server is not configured by default, so you won't receive the confirmation email during signup.

To manually confirm your account:

1. Find the confirmation link in the Django logs using `docker compose logs -f django`
2. Replace `example.com` by `localhost`on the URL and open it in your browser.

Another way is to go inside the Django containers and use commands like in [administrative procedures](Administrator-procedures.md).

### Troubleshooting storage endpoint URL

You may have to manually change the endpoint URL to have your local instance working. This may be an OS related issue.
Here is a possible fix:

1. `docker compose logs -f minio`
2. Grab the first one of these IP addresses:
```bash
minio_1           | Browser Access:
minio_1           |    http://172.27.0.5:9000  http://127.0.0.1:9000
```
3. Set `AWS_S3_ENDPOINT_URL=http://172.27.0.5:9000`in your `.env` file.

---

If static files are not loaded correctly, adding `DEBUG=True` to the `.env` file can help.


### For Apple CPU (M1, M2 chips)

In `docker-compose.yml`, replace in the `compute_worker` service:

```yaml title="docker-compose.yml"
command: bash -c "watchmedo auto-restart -p '*.py' --recursive -- celery -A compute_worker worker -l info -Q compute-worker -n compute-worker@%n"
```

by

```yaml title="docker-compose.yml"
command: bash -c "celery -A compute_worker worker -l info -Q compute-worker -n compute-worker@%n"
```


### Storage
By default, Codabench uses a built-in MinIO container. Some users may want a different solution, such as S3 or Azure. The configuration will vary slightly for each different type of storage.

For all possible supported storage solutions, see:
https://django-storages.readthedocs.io/en/latest/

### Remote Compute Workers
To set up remote compute workers, you can follow the steps described in our
[Compute Worker Management](../Organizers/Running_a_benchmark/Compute-Worker-Management---Setup.md) page.

## Troubleshooting

Read the following guide for troubleshooting: [How to deploy Codabench](How-to-deploy-Codabench-on-your-server.md#frequently-asked-questions-faqs).

Also, adding `DEBUG=True` to the `.env` file can help with troubleshooting the deployment.

Open a [Github issue](https://github.com/codalab/codabench/issues) to find help with your installation

## Online Deployement

For information about online deployment of Codabench, go to the [following page](How-to-deploy-Codabench-on-your-server.md)