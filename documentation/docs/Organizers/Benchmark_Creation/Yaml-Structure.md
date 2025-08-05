This page describes all the attributes in the Codabench competition definition language, using [YAML](https://yaml.org). This is used to create configuration files in Codabench competition bundles.

[Iris competition YAML file example!](https://github.com/codalab/competition-examples/blob/master/codabench/iris/competition.yaml)

## Versioning

A version for the YAML is required as this platform can support multiple versions of a `competition.yaml` file. For examples of v1.5 bundles, look [here](https://github.com/codalab/codalab-competitions/wiki/Organizer_Codalab-competition-YAML-definition-language).

For all v2 style competition bundles, be sure to add `version: 2` to the top of the competition.yml file.

**Note:** Not all features of v1.5 competitions are currently supported in v2.

## Competition Properties
### Required
- **title:** Title of the competition
- **image:** File path of competition logo, relative to `competition.yaml`
- **terms:** File path to a markdown or HTML page containing the terms of participation participants must agree to before joining a competition

### Optional
- **description:** A brief description of the competition.
- **registration_auto_approve:** True/False. If True, participation requests will not require manual approval by competition administrators. Defaults to False
- **docker_image:** Can specify a specific docker image for the competition to use. Defaults to `codalab/codalab-legacy:py3`. [More information here](Competition-docker-image.md).
- **make_programs_available:** Can specify whether to share the ingestion and scoring program with participants or not. Always available to competition organizer.
- **make_input_data_available:** Can specify whether to share the input data with participants or not. Always available to competition organizer.
- **queue:** Queue submissions are sent to. Can be used to specify competition specific compute workers. Defaults to the standard queue shared by all competitions. The queue should be referenced by its **Vhost**, not by its name. You can find the Vhost in `Queue Management` by clicking the eye button `View Queue Detail`.
- **enable_detailed_results:** True/False. If True, competition will watch for a `detailed_results.html` file and send its contents to storage. [More information here](Detailed-Results-and-Visualizations.md).
- **show_detailed_results_in_submission_panel:** a boolean (default: `True`) If set to `True`, participants can see detailed results in the submission panel
- **show_detailed_results_in_leaderboard:** a boolean (default: `True`) If set to `True`, participants can see detailed results in the leaderboard
- **contact_email:**  a valid contact email to reach the organizers.
- **reward:** a string to show the reward of the competition e.g. "$1000" for competition.
- **auto_run_submissions:** a boolean (default: `True`) if set to `False`, organizers have to manually run the submissions of each participant
- **can_participants_make_submissions_public:** a boolean (default: `True`) if set to `False`, participants cannot make their submissions public from submissions panel.
- **forum_enabled:** a boolean (default: `True`) if set to `False`, organizers and participants cannot see or interact with competition forum.
 



```yaml
# Required
version: 2
title: Compute Pi
image: images/pi.png
terms: pages/terms.md

# Optional
description: Calculate pi to as many digits as possible, as quick as you can.
registration_auto_approve: True
docker_image: codalab/codalab-legacy:py37 # default docker image
make_programs_available: True
make_input_data_available: False
enable_detailed_results: True
show_detailed_results_in_submission_panel: True
show_detailed_results_in_leaderboard: True
contact_email: organizer_email@example.com
reward: $1000 prize pool
auto_run_submissions: True
can_participants_make_submissions_public: False
forum_enabled: True
```

## Pages
### Required
- **title:** String that will be displayed in the competition detail page as the title of the page
- **file:** File path to a markdown or HTML page relative to competition.yaml containing the desired content of the page.

```yaml
pages:
  - title: Welcome
    file: welcome.md
  - title: Getting started
    file: pages/getting_started.html
```

## Phases
### Required
- **name:** Name of the phase
- **start:** Datetime string for the start of the competition. ISO format strings are recommended. Use `YYYY-MM-DD HH:MM:SS` date-time format. (Example date-time: 2024-12-31 14:30:00)
- **end:** Datetime string for the end of the phase (optional for _last phase only._ If not supplied for the final phase, that phase continues indefinitely). Use `YYYY-MM-DD HH:MM:SS` date-time format. (Example date-time: 2024-12-31 14:30:00)
- **tasks:** An array of numbers pointing to the index of any defined tasks relevant to this phase (see tasks for more information)


### Optional
- **index:** Integer for noting the order of phases, Phases _must_ be sequential, without any overlap. If indexes are not supplied, ordering will be assumed by declaration order.
- **max_submissions:** Total submissions allowed per participant for the entire phase
- **max_submissions_per_day:** Submission limit for each participant for a given day
- **auto_migrate_to_this_phase:** Cannot be set on the first phase of the competition. This will re-submit all successful submissions from the previous phase to this phase at the time the phase starts.
- **execution_time_limit:** Execution time limit for submissions, given in seconds. Default is 600.
- **hide_output:** True/False. If True, stdout/stderr for all submissions to this phase will be hidden from users who are not competition administrators or collaborators.
- **hide_prediction_output:** True/False. If True, participants won't be able to download the "Output from prediction step".
- **hide_score_output:** True/False. If True, participants won't be able to download the "Output from scoring step" containing the `scores.txt` file.
- **starting_kit:** path to the starting kit, a folder that participants will be able to download. Put there any useful files to help participants (example submissions, notebooks, documentation).
- **public_data:** path to public data, that participants will be able to download.
- **accepts_only_result_submissions**(default=False): When set to True, the phase is expected to accept only result submissions.

```yaml
phases:
  - index: 0
    name: Development Phase
    description: Tune your models
    start: 2019-12-12 13:30:00  # Time in UTC+0 and 24-hour format
    end: 2020-02-01 00:00:00  # Time in UTC+0 and 24-hour format
    execution_time_limit: 1200
    starting_kit: starting_kit
    public_data: public_data
    accepts_only_result_submissions: True
    tasks:
      - 0
  - index: 1
    name: Final Phase
    description: Final testing of your models
    start: 2020-02-02 00:00:00 # Time in UTC+0 and 24-hour format
    auto_migrate_to_this_phase: True
    accepts_only_result_submissions: False
    tasks:
      - 1
```

## Tasks
### Required
- **index:** Number used for internal reference of the task, pointed to by solutions (below) and phases (above)
- **name:** Name of the Task
- **scoring_program:** File path relative to `competition.yaml` pointing to a `.zip` file or an unzipped directory, containing the scoring program

OR

- **key:** UUID of a task already in the database. **If key is provided, all fields other than index will be ignored**

### Optional
- **description:** Brief description of the task
- **input_data:** File path to the data to be provided during the prediction step
- **reference_data:** File path to the data to be provided to the scoring program
- **ingestion_program:** File path to the ingestion program files
- **ingestion_only_during_scoring:** True/False. If true, the ingestion program will be run in parallel with the scoring program, and can communicate w/ the scoring program via a shared directory

```yaml
tasks:
  - index: 0
    name: Compute Pi Developement Task
    description: Compute Pi, focusing on accuracy
    input_data: dev_phase/input_data/
    reference_data: dev_phase/reference_data/
    ingestion_program: ingestion_program.zip
    scoring_program: scoring_program.zip
  - index: 1
    name: Compute Pi Final Task
    description: Compute Pi, speed and accuracy matter
    input_data: final_phase/input_data/
    reference_data: final_phase/reference_data/
    ingestion_program: ingestion_program.zip
    scoring_program: scoring_program.zip
```

## Solutions
### Required
- **index:** Index number of solution
- **tasks:** Array of the tasks (referenced internally) for which this solution applies.
- **path:** File path to `.zip` or directory containing the solution data.

```yaml
solutions:
  - index: 0
    path: solutions/solution1.zip
    tasks:
    - 0
    - 1
  - index: 1
    path: solutions/solution2/
    tasks:
    - 0
```

## Fact Sheet
### Optional
JSON for asking metadata questions about each submission when they are submitted
- **KEY:** Programmatic name for a response. Should not contain any whitespace.
- **QUESTION TYPE:**
   - **"checkbox":** Prompts the user with a checkbox for a yes/no or true/false type question
      - **_Required_ SELECTION**: [true, false]
    - **"text":**: Prompts the user with a text box to write a response.
      - **_Required_ SELECTION**: ""
      - `"is_required": "false"` will allow the user not to submit a response. Otherwise, the user will have to type something.
    - **"select":** Gives the user a dropdown to select a value from.
      - **SELECTION**: Give an array of comma separated values that the user can select from: ["Value1","Value2","Value3",...,"ValueN"]
      - TIP: If you want this selection to be optional you can add "" as an option. ex. ["", "Value1", ...] and set `"is_required": "false"`
- `is_on_leaderboard:` setting this to "true" will show this response on the leaderboard along with their submission.

### Structure
```yaml
fact_sheet: {
    "[KEY]": {
        "key": "[KEY]",
        "type": "[QUESTION TYPE]",
        "title": "[DISPLAY NAME]",
        "selection": [SELECTION],
        "is_required": ["true" OR "false"],
        "is_on_leaderboard": ["true" OR "false"]
}
```

```yaml
fact_sheet: {
    "bool_question": {
        "key": "bool_question",
        "type": "checkbox",
        "title": "boolean",
        "selection": [True, False],
        "is_required": "false",
        "is_on_leaderboard": "false"
    },
    "text_question": {
        "key": "text_question",
        "type": "text",
        "title": "text",
        "selection": "",
        "is_required": "false",
        "is_on_leaderboard": "false"
    },
    "text_required": {
        "key": "text_required",
        "type": "text",
        "title": "text",
        "selection": "",
        "is_required": "true",
        "is_on_leaderboard": "false"
    },
    "selection": {
        "key": "selection",
        "type": "select",
        "title": "selection",
        "selection": ["", "v1", "v2", "v3"],
        "is_required": "false",
        "is_on_leaderboard": "true"
    }
}
```


## Leaderboards
### Leaderboard Details

### Required
- **title:** Title of leaderboard
- **key:** Key for scoring program to write to
- **columns:** An array of columns (see column layout below)

### Optional
- **submission_rule:** "Add", "Add_And_Delete", "Add_And_Delete_Multiple", "Force_Last", "Force_Latest_Multiple" or "Force_Best". It sets the behavior of the leaderboard regarding new submissions. See [Leaderboard Functionality](Leaderboard-Functionality.md) for more details.
- **hidden:** True/False. If True, the contents of this leaderboard will be hidden to all users who are not competition administrators or collaborators.

## Column Details

### Required
- **title:** Title of the column
- **key:** Key for the scoring program to write to. The keys must match the keys of the `scores.json` file returned by the scoring program, as explained with more details [here](Competition-Bundle-Structure.md#scoring-program).
- **index:** Number specifying the order the column should show up on the leaderboard

### Optional
- **sorting:** sorting order for the column: Descending (desc) or Ascending (asc)
  - Ascending: smaller scores are better
  - Descending: larger scores are better
- **computation:** computation to be applied *must be accompanied by computation indexes*
  - computation options: sum, avg, min, max
- **computation_indexes:** an array of indexes of the columns the computation should be applied to
- **precision:** (*integer, default=2*) to round the score to *precision* number of digits
- **hidden:** (*boolean, default=False*) to hide/unhide a column on leaderboard

```yaml
leaderboards:
  - title: Results
    key: main
    submission_rule: "Force_Last"
    columns:
      - title: Accuracy Score 1
        key: accuracy_1
        index: 0
        sorting: desc
        precision: 2
        hidden: False
      - title: Accuracy Score 2
        key: accuracy_2
        index: 1
        sorting: desc
        precision: 3
        hidden: False
      - title: Max Accuracy
        key: max_accuracy
        index: 2
        sorting: desc
        computation: max
        precision: 3
        hidden: False
        computation_indexes:
          - 0
          - 1
      - title: Duration
        key: duration
        index: 3
        sorting: asc
        precision: 2
        hidden: False
```