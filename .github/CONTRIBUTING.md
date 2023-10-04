# HOW YOU CAN CONTRIBUTE TO THE CODABENCH PROJECT

## First step: being a codabench user.

- create a user account on https://codalab.lisn.fr and on https://codabench.org.
- register on https://codabench.org to this existing competition (IRIS-tuto) https://www.codabench.org/competitions/1115/  and make a submission (from https://github.com/codalab/competition-examples/tree/master/codabench/iris): sample_result_submission and sample_code_submission. See https://github.com/codalab/codabench/wiki/User_Participating-in-a-Competition
- create your own private competition (from https://github.com/codalab/competition-examples/tree/master/codabench/ ). See https://github.com/codalab/codabench/wiki/Getting-started-with-Codabench

 ## Second step: setting a local instance of Codabench.

- Follow the tutorial in codabench wiki: https://github.com/codalab/codabench/wiki/Codabench-Installation. According to your hosting OS, you might have to tune your environment file a bit. Try without enabling the SSL protocol (doing so, you don't need a domain name for the server). Try using the embedded Minio storage solution instead of a private cloud storage.
- if needed, you can also look into https://github.com/codalab/codabench/wiki/How-to-deploy-Codabench-on-your-server

## Third step: using one's local instance

- create your own competition and play with it. You can look at the output logs of each different docker container.
- setting you as an admin of your platform (https://github.com/codalab/codabench/wiki/Administrator-procedures#give-superuser-privileges-to-an-user) and visit the Django Admin menu: https://github.com/codalab/codabench/wiki/Administrator-procedures#give-superuser-privileges-to-an-user

## Fourth step: setting an autonomous computer-worker on your PC

- configure and launch the docker container: https://github.com/codalab/codabench/wiki/Compute-Worker-Management---Setup
- create a private queue on your new own competition on the production server codabench.org: https://github.com/codalab/codabench/wiki/Queue-Management#create-queue
- assign your own compute-worker to this private queue instead of the default queue.
