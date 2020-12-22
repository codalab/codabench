## GET READY

- This new platform is an upgraded version of [Codalab](https://competitions.codalab.org/) allowing you to create either competitions or benchmarks
- This getting started tutorial shows you a simple example of how to create a competition (fancier examples can be found [here](https://github.com/codalab/competitions-v2/tree/codabench/sample_bundle/src/tests/functional/test_files/AutoWSL_sample); the full documentation is [here](https://github.com/codalab/competitions-v2/wiki))
- Create a Codalab account (if not done yet)
- Download the [sample competition bundle](https://github.com/codalab/competitions-v2/tree/develop/docs/competition.zip) and a [sample submission](https://github.com/codalab/competitions-v2/tree/develop/docs/submission.zip)
- Do not unzip them.

## WHAT'S EXPECTED AFTER THIS TUTORIAL

- a working [competition/benchmark](https://www.codabench.org/competitions/214/)
- you can submit [submission.zip](https://github.com/codalab/competitions-v2/tree/develop/docs/submission.zip) for playing with
- we have enabled "Auto approve registration requests" so that anyone could join without approval

## CREATE A COMPETITION

- From the front page [https://www.codabench.org/](https://www.codabench.org/) top menu, go to the Benchmark > Management
- Click the green “Upload” button at the top right.
- Upload the sample competition bundle => this will create your competition.

## MAKE A SUBMISSION

- In your competition page, go to the tab “My submissions”
- Submit the sample submission bundle.
- When your submission finishes, go to the Result tab to check it shows up on the leaderboard.

## MAKE CHANGES

- Click on the Edit gray button at the top the enter the editor
- Change the logo
- Save your changes

## Composition of the competition bundle

### metadata file

- competition.yaml: contains ALL the configurations of your benchmark/competition

### datasets

- input_data: contains datasets for training models and datasets for testing models (i.e. X_train, y_train, X_test)
- reference_data: answers to training Datasets (i.e. y_test)

### core logic

- ingestion_program: defines the logic of how to read user submissions, read your data, train the model and inferences outputs
- scoring_program: defines the logic of how to calculate user submissions score

### static files

- participate.md: markdown file about how to participate in this benchmark/competition
- terms.md: about the terms and conditions of the benchmark, this will show up when other participants join the benchmark/competition
- wheat.jpg: logo for this benchmark/competition

You are done with this simple tutorial.

Next, check the more [advanced tutorial](https://github.com/codalab/competitions-v2/tree/develop/docs/tutorial)