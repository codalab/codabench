A competition bundle is simply a zip file containing the `competition.yaml` which defines different aspects and attributes of your competition such as the logo, the html/markdown pages documenting your competition, and the data associated with your competition.

## What is a Competition?
A competition is composed of a phase or many phases defining the active times of the competition, along with some other settings such as execution time limit. Each phase can have one or more tasks. 

A task is the problem the submission should be solving, therefore submissions that solve a task can be thought of as a solution. A task consists of reference data, input data, scoring program, and an ingestion program. 

For starting kits in v2, they should be solutions included with the competition bundle. See the example `competiton.yaml` or the section Competition YAML below for a link with more info. For more information on the different types of data, see the lower section of this page.

## Example Competition Bundle Layout:

**[Some competition bundle examples!](https://github.com/codalab/competition-examples/tree/master/codabench)**

!!! Note
    Files can be under a directory, they just have to be referenced by their full path in the YAML. See the Competition YAML section below.

```
--\ example_competition.zip
  |
  |- competition.yaml
  |- logo.png
  |- example_reference_data.zip
  |- example_scoring_program.zip
  |- example_solution.zip
  |- overview.md
  |- evaluation.md
  |- terms_and_conditions.md
  |- data.md
```


## Example competition.yaml:
```yaml title="competition.yaml"
title: Example Competition Submit Scores
description: An example competition where submissions should output the score they want
image: logo.jpg
terms: terms.md
pages:
    - title: overview
      file: overview.md
    - title: evaluation
      file: evaluation.md
    - title: terms
      file: terms_and_conditions.md
    - title: data
      file: data.md
phases:
    - index: 0
      name: First phase
      description: An example phase
      start: 2018-03-01
      end: 2027-03-01
      tasks:
        - 0
tasks:
    - index: 0
      name: First Phase Task
      description: Task for the first phase
      scoring_program: example_scoring_program.zip
      reference_data: example_reference_data.zip
solutions:
    - index: 0
      path: example_solution.zip
      tasks:
        - 0
leaderboard:
  - title: Results
    key: main
    columns:
      - title: score
        key: score
        index: 0
        sorting: desc
```


## Competition YAML
The `competition.yaml` file is the most important file in the bundle. It's what Codabench looks for to figure out the structure and layout of your competition, along with additional details. For more information on setting up a `competition.yaml` see the docs page here:
[Competition YAML](https://docs.codabench.org/latest/Organizers/Benchmark_Creation/Yaml-Structure/)


## Data Types And Their Role:

### Reference Data:
Reference data is typically the truth data that your participant's predictions are compared against.

### Scoring Program
The scoring program is the file that gets ran to determine the scores of the submission, typically either based on the submission's prediction outputs, or the results from the submission itself when compared with the reference data. Usually this should be a script like a python file, but it can generally be anything.

This is also paired with a `metadata.yaml` file with a key `command` that correlates to the command used to run your scoring program. There are also special directories available for use. 

Example:
Here's what a `metadata.yaml` might look like:
```yaml title="metadata.yaml"
command: python3 /app/program/scoring.py /app/input/ /app/output/
```

This specifies that python3 is going to run the scoring program (which is going to be located in /app/program/scoring.py).
It also gives, as `args`:
- The input folder, which contains either the user's own results or predictions from ingestion
- The output folder where the score is placed. 

The arguments are optional, but passing them may be more convenient.

The scoring program outputs a `scores.json` file containing the results for each column of the leaderboard. After computing a submission, this file should look like something like this:

```json title="scores.json"
{"accuracy": 0.886, "duration": 42.4}
```

The keys should match the leaderboard columns keys defined in [the `competition.yaml` file](Yaml-Structure.md#leaderboards).

The scoring program can also output detailed results as an HTML file for each submission. [Click here for more information](Detailed-Results-and-Visualizations.md).

### Ingestion Program
The ingestion program is a file that gets ran to generate the predictions from the submissions if necessary. This is usually a python script or a script in another language, but it can generally be anything.

The ingestion program is also paired with a `metadata.yaml` that specifies how to run it. It should have a key `command` that is the command used to run your ingestion program. The same special directories should be available to your ingestion program. 

Example: Here's what an ingestion `metdata.yaml` might look like this:
```yaml title="metadata.yaml"
command: python3 /app/program/ingestion.py /app/input_data/ /app/output/ /app/program /app/ingested_program
```

Just like the example above, this specifies we're using python to run our ingestion program. Please note that it is not necessary to pass these directories as arguments to the programs, but it can be convenient. More information about the folder layout [here](../../Developers_and_Administrators/Submission-Docker-Container-Layout.md#submission-container).

### Input Data
This is usually the test data used to generate predictions from a user's code submission when paired with an ingestion program.
