When you make a submission to Codabench, the information and file are saved to the database. Afterwards, a Celery task gets sent to the compute worker (Default queue or a compute worker attached to a custom queue). From there the compute worker spins up another docker container with either the default docker image for submissions, or a custom one supplied by the organizer.

## Site Worker
The site worker can be thought of exactly how it sounds. It's a local celery worker for the site to handle different Celery tasks and other miscellaneous functions. This is what is responsible for creating competition dumps, unpacking competitions, firing off the tasks for re-running submissions, etc.

## Compute Worker
Is a remote and/or local celery worker that listens to the main RabbitMQ server for tasks. A compute worker can be given a special queue to listen to, or listen to the default queue. For more information on setting up a custom queue and compute worker, see:

- [Queue Management](../Organizers/Running_a_benchmark/Queue-Management.md)
- [Compute Worker Management and Setup](../Organizers/Running_a_benchmark/Compute-Worker-Management---Setup.md)

## Submission Container
The submission container is the container that participant's submissions get ran in. The image used to create this container is either the Codabench default if the organizer's haven't specified an image, or the custom image they specified in the competition.
The default docker image is `codalab/codalab-legacy:py37`. Organizers can specify their own image using either the [YAML file](../Organizers/Benchmark_Creation/Yaml-Structure.md) or the [editor](../Organizers/Running_a_benchmark/Competition-Management-&-List.md#edit-competition-button).

This container is also created with some specific directories, some of which are only available at specific steps of the run. For example, generally for a submission there are 2 steps. The prediction step (If the submission needs to make predictions) and the scoring step, where the predictions are scored against the truth reference data.

Here are the following directories:

 - `/app/input_data` Where input data will be (Only exists if input data is supplied for the task)
 - `/app/output` Where all submission output should go (Should always exist)
 - `/app/ingestion_program` Where the ingestion program files should exist (Only available in ingestion)
 - `/app/program` Where the scoring program and/or the ingestion program should be located (Should always exist)
 - `/app/input` Where any input for this step should be. (I.E: Previous predictions from ingestion for scoring. Only exists on scoring step)
 - `/app/input/ref` Where the reference data should live (Not available to submissions. Only available on scoring step.)
 - `/app/input/res` Where predictions/output from the prediction step should live. (Only available on scoring step)
 - `/app/shared` Where any data that needs to be shared between the ingestion program and submission should exist. (Only available on scoring steps.)
 - `/app/ingested_program` Where submission code should live if it is a code submission. (Only available in ingestion)