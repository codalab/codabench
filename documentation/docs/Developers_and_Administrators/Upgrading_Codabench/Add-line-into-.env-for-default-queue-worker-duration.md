!!! note "This intervention is needed when upgrading from a version equal or lower than [v1.7.0](https://github.com/codalab/codabench/releases/tag/v1.7.0)"

You will need to add the following line into your `.env` file
```ini title=".env"
MAX_EXECUTION_TIME_LIMIT=600 # time limit for the default queue (in seconds)
```

This will change the maximum time a job can run on the default queue of your instance, as noted [here](https://github.com/codalab/codabench/pull/1154)