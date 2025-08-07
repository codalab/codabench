```bash
# Without "end to end" tests
$ docker compose exec django py.test -m "not e2e"

# "End to end tests" (a shell script to launch a selenium docker container)
$ ./run_selenium_tests.sh

# If you are on Mac OSX it is easy to watch these tests, no need to install
# anything just do:
$ open vnc://0.0.0.0:5900

# And login with password "secret"
```

## CircleCI

To simulate the tests run by CircleCI locally, run the following command:

```sh
docker compose -f docker-compose.yml -f docker-compose.selenium.yml exec django py.test src/ -m "not e2e"
```

## Example competitions

The repo comes with a couple examples that are used during tests:

### v2 test data
 ```
 src/tests/functional/test_files/submission.zip
 src/tests/functional/test_files/competition.zip
 ```
### v1.5 legacy test data
 ```
 src/tests/functional/test_files/submission15.zip
 src/tests/functional/test_files/competition15.zip
 ```
 
### Other Codalab Competition examples
[https://github.com/codalab/competition-examples/tree/master/v2/](https://github.com/codalab/competition-examples/tree/master/v2/)