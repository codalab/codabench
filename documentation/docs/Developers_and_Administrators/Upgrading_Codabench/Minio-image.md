!!! note "After upgrading from Codabench <1.21.1, you will need to migrate MinIO and upgrade compute workers."

### 1. MinIO migration (depending on setup)
If you are running MinIO locally (defined by `.env` and `docker-compose.yml`), you may need to follow the MinIO upgrade instructions to duplicate and mirror your buckets and convert them to the new format:
https://docs.min.io/community/minio-object-store/operations/deployments/baremetal-migrate-fs-gateway.html

### 2. Upgrade compute workers

See [Upgrade compute workers](index.md#upgrade-compute-workers).
