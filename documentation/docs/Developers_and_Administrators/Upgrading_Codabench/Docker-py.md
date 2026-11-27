!!! note "After upgrading from Codabench <1.22.0, you will need to add an environment variable and upgrade compute workers."

## Main Instance
There is a new environment variable for the contact email:
```
CONTACT_EMAIL=info@codabench.org
```
Make sure to add it to your `.env` file before launching the containers.

## Compute Workers
Major compute worker changes require updating the compute worker images for both Docker and Podman: see [Upgrade compute workers](index.md#upgrade-compute-workers). Podman workers also need Podman 5.4 minimum on the host.
