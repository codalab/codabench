# HOW YOU CAN CONTRIBUTE TO THE CODABENCH PROJECT

## 1. Being a Codabench user.

- Create a user account on https://codalab.lisn.fr and on https://codabench.org.
- Register on https://codabench.org to this existing competition (IRIS-tuto) https://www.codabench.org/competitions/1115/  and make a submission (from https://github.com/codalab/competition-examples/tree/master/codabench/iris): sample_result_submission and sample_code_submission. See https://docs.codabench.org/latest/Participants/User_Participating-in-a-Competition/ 
- Create your own private competition (from https://github.com/codalab/competition-examples/tree/master/codabench/ ). See https://docs.codabench.org/latest/Organizers/Benchmark_Creation/Getting-started-with-Codabench/

 ## 2. Setting a local instance of Codabench.

- Follow the tutorial in codabench docs: https://docs.codabench.org/latest/Developers_and_Administrators/Codabench-Installation/. According to your hosting OS, you might have to tune your environment file a bit. Try without enabling the SSL protocol (doing so, you don't need a domain name for the server). Try using the embedded Minio storage solution instead of a private cloud storage.
- If needed, you can also look into https://docs.codabench.org/latest/Developers_and_Administrators/How-to-deploy-Codabench-on-your-server/ 

## 3. Using one's local instance

- Create your own competition and play with it. You can look at the output logs of each different docker container.
- Setting you as an admin of your platform (https://docs.codabench.org/latest/Developers_and_Administrators/Administrator-procedures/#give-superuser-privileges-to-a-user) and visit the Django Admin menu: https://docs.codabench.org/latest/Developers_and_Administrators/Administrator-procedures/#give-superuser-privileges-to-a-user
## 4. Setting an autonomous computer-worker on your PC

- Configure and launch the docker container: https://docs.codabench.org/latest/Organizers/Running_a_benchmark/Compute-Worker-Management---Setup/ 
- Create a private queue on your new own competition on the production server codabench.org: https://docs.codabench.org/latest/Organizers/Running_a_benchmark/Queue-Management/#create-queue
- Assign your own compute-worker to this private queue instead of the default queue.
