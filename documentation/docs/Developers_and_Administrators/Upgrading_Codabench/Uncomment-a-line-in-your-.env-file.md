!!! note "This intervention is needed when upgrading from a version equal or lower than [v1.8.0](https://github.com/codalab/codabench/releases/tag/v1.8.0)"


After the Caddy upgrade, you will need to uncomment a line in your `.env` file:
```ini title=".env"
TLS_EMAIL = "your@email.com"
```
More information [here](https://github.com/codalab/codabench/pull/1424)