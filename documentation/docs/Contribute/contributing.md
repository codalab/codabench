## Being a Codabench user

- Create a user account on [Codabench](https://codabench.org)
- Register on [Codabench](https://codabench.org) to this existing competition [IRIS-tuto](https://www.codabench.org/competitions/1115/)  and make a submission (you can find the necessary files [here](https://github.com/codalab/competition-examples/tree/master/codabench/iris)): `sample_result_submission` and `sample_code_submission`. See [this page](../Participants/User_Participating-in-a-Competition.md) for more information.
- Create your own private competition (you can find the necessary files [here](https://github.com/codalab/competition-examples/tree/master/codabench/) ). See [this page](../Organizers/Benchmark_Creation/Getting-started-with-Codabench.md) for more information.

## Setting up a local instance of Codabench

- Follow the tutorial in codabench [Docs](../Developers_and_Administrators/Codabench-Installation.md). According to your hosting OS, you might have to tune your environment file a bit. Try without enabling the SSL protocol (doing so, you don't need a domain name for the server). Try using the embedded Minio storage solution instead of a private cloud storage.
- If needed, you can also look into [How to deploy Codabench on your server](../Developers_and_Administrators/How-to-deploy-Codabench-on-your-server.md)

### Using your local instance

- Create your own competition and play with it. You can look at the output logs of each different docker container.
- Setting you as an [admin](../Developers_and_Administrators/Administrator-procedures.md#give-superuser-privileges-to-a-user) of your platform and visit the Django Admin menu.

## Setting up an autonomous Compute Worker on a machine

- Configure and launch a [compute worker](../Organizers/Running_a_benchmark/Compute-Worker-Management---Setup.md) docker container.
- Create a private [Queue](../Organizers/Running_a_benchmark/Queue-Management.md#create-queue) on your new own competition on the production server codabench.org
- Assign your own compute-worker to this private queue instead of the default queue.
