![Codabench logo](src/static/img/codabench_black.png) [![Circle CI](https://circleci.com/gh/codalab/codabench.svg?style=shield)](https://app.circleci.com/pipelines/github/codalab/codabench)

## Major changes to upstream

* Created a django admin command for creating users and approving them for a competition, given a list of users/emails.
* Replaced organization logos on homepage with ScaDS.AI logo.
* Adjusted Caddyfile for external account binding.
* Enabled TLS/HTTPS for minio by sharing the certificates from caddy.
  They currently need to be **copied manually** when the certificate gets renewed, using something like
  ```
  mkdir -p certs/minio && sudo cp -a caddy_data/caddy/certificates/acme.sectigo.com-v2-ov/hackathon.scads.ai/hackathon.scads.ai.key $_/private.key
  mkdir -p certs/minio && sudo cp -a caddy_data/caddy/certificates/acme.sectigo.com-v2-ov/hackathon.scads.ai/hackathon.scads.ai.crt $_/public.crt
  ```
  Should likely instead either copy it automatically or reverse proxy to minio.

## Extra deployment instructions

### Development

* Add `127.0.0.1	minio` to `/etc/hosts`.

### Production

* In addition to port 443, open at least port tcp/9000.
* It seems it is not necessary to set the public bucket to read and write, as it is described in the deployment instructions.
* The following service is used but it might not be necessary (anymore).

  ```
  # /etc/systemd/system/keep_codabench_worker_running.service

  [Unit]
  Description=Start the Codabench compute worker again because sometimes it shuts down (either because connection loss or because of the VM causing it somehow)

  [Service]
  Type=oneshot
  ExecStart=/usr/bin/docker compose -f /home/hackathon/DIRECTORY HERE/docker-compose.yml up -d compute_worker
  ```

  ```
  # /etc/systemd/system/keep_codabench_worker_running.timer

  [Unit]
  Description=Restart Codabench compute_worker container every hour

  [Timer]
  OnCalendar=*:0/30

  [Install]
  WantedBy=timers.target
  ```

## What is Codabench?

Codabench is an open-source web-based platform that enables researchers, developers, and data scientists to collaborate, with the goal of advancing research fields where machine learning and advanced computation is used. Codabench helps to solve many common problems in the arena of data-oriented research through its online community where people can share worksheets and participate in competitions and benchmarks. It can be seen as a version 2 of [CodaLab Competitions](https://github.com/codalab/codalab-competitions).

To see Codabench in action, visit [codabench.org](https://www.codabench.org/).


## Documentation

- [Codabench Wiki](https://github.com/codalab/codabench/wiki)


## Quick installation (for Linux)

_To participate, or even organize your own benchmarks or competitions, **you don't need to install anything**, you just need to sign in an instance of the platform (e.g. [this one](https://www.codabench.org/)).
If you wish to configure your own instance of Codabench platform, here are the instructions:_


```
$ cp .env_sample .env
$ docker compose up -d
$ docker compose exec django ./manage.py migrate
$ docker compose exec django ./manage.py generate_data
$ docker compose exec django ./manage.py collectstatic --noinput
```

You can now login as username "admin" with password "admin" at http://localhost/

If you ever need to reset the database, use the script `./reset_db.sh`

For more information about installation, checkout [Codabench Basic Installation Guide](https://github.com/codalab/codabench/wiki/Codabench-Installation) and [How to Deploy Server](https://github.com/codalab/codabench/wiki/How-to-deploy-Codabench-on-your-server).


## License

Copyright (c) 2020-2022, Université Paris-Saclay.
This software is released under the Apache License 2.0 (the "License"); you may not use the software except in compliance with the License.

The text of the Apache License 2.0 can be found online at:
http://www.opensource.org/licenses/apache2.0.php


## Cite Codabench in your research

```
@article{codabench,
    title = {Codabench: Flexible, easy-to-use, and reproducible meta-benchmark platform},
    author = {Zhen Xu and Sergio Escalera and Adrien Pavão and Magali Richard and
              Wei-Wei Tu and Quanming Yao and Huan Zhao and Isabelle Guyon},
    journal = {Patterns},
    volume = {3},
    number = {7},
    pages = {100543},
    year = {2022},
    issn = {2666-3899},
    doi = {https://doi.org/10.1016/j.patter.2022.100543},
    url = {https://www.sciencedirect.com/science/article/pii/S2666389922001465}
}
```
