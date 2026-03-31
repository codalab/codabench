!!! note "After upgrading from Codabench <1.22.0, you will need to rebuild containers, run Django migrations and upgrade compute workers."


## Main Instance
Some of the changes will require a migration and `collectstatic` commands to be run: 
```sh
docker compose build && docker compose up -d
docker compose exec django python manage.py migrate
docker compose exec django python manage.py collectstatic --no-input
```


There is a new environment variable for the contact email:
```
CONTACT_EMAIL=info@codabench.org
```
Make sure to add it to your `.env` file before launching the containers

## Compute Workers
Major compute workers changes will require updating the Compute Worker images for both Docker and Podman. Podman workers will also need Podman 5.4 minimum to work on the host
