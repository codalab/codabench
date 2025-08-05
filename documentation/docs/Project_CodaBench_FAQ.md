
## General questions

### What is Codabench for?
Codabench benchmarks are aimed at researchers, scientists and other professionals who want to track algorithm performance via benchmarks or have participants participate in a competition to find the best solution to a problem. We run a free public instance at [https://www.codabench.org/](https://www.codabench.org/) and the raw code is on [Github](https://github.com/codalab/codabench).


### Can CodaLab competitions be privately hosted?
Yes, you can host your own CodaLab instance on a private or hosted server (e.g. Azure, GCP or AWS). For more information, see [how to deploy Codabench on your server](Developers_and_Administrators/How-to-deploy-Codabench-on-your-server.md) and [local installation](Developers_and_Administrators/Codabench-Installation.md) guide. However, most benchmark organizers do NOT need to run their own instance. If you run a computationally demanding competition, you can hook up your own [compute workers](Organizers/Running_a_benchmark/Compute-Worker-Management---Setup.md) in the backend very easily. 


### How to change my username?
You cannot change your username BUT you can change your display name which will then be displayed instead of your username. To change your display name, follow these instructions:

    1. Login to Codabench
    2. Click your username in the top right corner
    3. Click `Edit Profile` in the list
    4. Set a display name you want to use
    5. Click `Submit` button to save changes

### How to make a task public or use public tasks from other users?
Follow the detailed instruction [here](Organizers/Benchmark_Creation/Public-Tasks-and-Tasks-Sharing.md) to know how you can make your task public and use other public tasks in your competitions.

### How to delete my account?
Click on your account name on the top right of the website, then on `account`



***

## Technical questions

### Server Setup Issues
Many technical FAQ are already located in the [deploy your own server instructions.](Developers_and_Administrators/How-to-deploy-Codabench-on-your-server.md)

Questions already answered there:

- Getting `Invalid HTTP method` in django logs.
- I am missing some static resources (css/js) on front end.
- CORS error when uploading bundle.
- Logos don't upload from minio.
- Compute worker execution with insufficient privileges
- Securing Codabench and Minio


### A library is missing in the docker environment. What do to?


#### How does Codabench use dockers?
When you submit code to the Codabench platform, your code is executed inside a docker container. This environment can be exactly reproduced on your local machine by downloading the corresponding docker image.

#### For participants

- If you are a **competition participant**, contact the competition organizers to ask them if they can add the missing library or program. They can either accept or refuse the request.

#### For organizers
- If you are a **competition organizer**, you can select a different competition docker image. If the default docker image (`codalab/codalab-legacy:py37`) does not suits your needs, you can either:
    - Select another image from DockerHub
    - Create a new image from scratch
    - Edit the default image and push it to your own DockerHub account

[More information here](Organizers/Benchmark_Creation/Competition-docker-image.md).

### Emails are not showing up in my inbox for registration
When deploying a local instance, the email server is not configured by default, so you won't receive the confirmation email during signup. In `.env` towards the bottom you will find:
```ini title=".env" 
# Uncomment to enable email settings
#EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
#EMAIL_HOST=smtp.sendgrid.net
#EMAIL_HOST_USER=user
#EMAIL_HOST_PASSWORD=pass
#EMAIL_PORT=587
#EMAIL_USE_TLS=True
```

Uncomment and fill in SMPT server credentials. A good suggestion if you've never done this is to use [sendgrid](https://sendgrid.com/).

### Robots and automated submissions?
What about robot policy, reckless, or malicious behavior?
Codabench does not forbid the use of [robots](Developers_and_Administrators/Robot-submissions.md) (bots) to access the website, provided that it is not done with malicious intentions to disturb the normal use and jam the system. A user who abuses their rights by knowingly, maliciously, or recklessly jamming the system, causing the system to crash, causing loss of data, or gaining access to unauthorized data, will be banned from accessing all Codabench services.

