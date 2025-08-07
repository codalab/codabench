For specific information on leaderboard and column fields, see the explanations in the [YAML structure](Yaml-Structure.md#leaderboards).

## Writing scores
A leaderboard and column are written to via their keys.
A leaderboard declaration like so
```yaml
leaderboard:
  - title: Results
    key: main
    submission_rule: "Force_Last"
    columns:
      - title: Accuracy Score 1
        key: accuracy_1
        index: 0
        sorting: desc
      - title: Accuracy Score 2
        key: accuracy_2
        index: 1
        sorting: desc
      - title: Max Accuracy
        key: max_accuracy
        index: 2
        sorting: desc
        computation: max
        computation_indexes:
          - 0
          - 1
      - title: Duration
        key: duration
        index: 3
        sorting: asc
```
would require, via the scoring program, the following `scores.json` file
```json title="scores.json"
{"accuracy_1": 0.5, "accuracy_2": 0.75, "duration": 123.45}
```
This is the end result shown on the leaderboard:
```
| Accuracy Score 1 | Accuracy Score 2 | Max Accuracy | Duration |
|:----------------:|:----------------:|:------------:|:--------:|
|              0.5 |             0.75 |         0.75 |   123.45 |
```

## Computation
Scores should not be written to computation columns, instead they will be calculated by the platform at the time scores are read from `scores.json`.

Computation options are: 
  - sum
  - avg
  - min
  - max

These are applied across the columns specified as `computation_indexes`.

So in the example above, the computation option specified is `max` and the indexes are 0 and 1, meaning we will take the max score of columns at index 0 and 1 (i.e: .5 and .75) so .75 is returned in the computation.

## Primary columns
**Ranking is determined first by the primary column of the leaderboard**. In the `competition.yaml`, this is the column at index 0. This option can be changed in the competition editor.
After sorting scores by the primary column (asc or desc as specified on the column) sorting then continues from left to right. Final sorting is done by the `submitted_at` timestamp, so that if submissions have identical scores (as in the case of baselines), the earlier submissions will be ranked higher.

Example (with Max Accuracy set as the primary column):
```
| Rank | Accuracy Score 1 | Accuracy Score 2 | Max Accuracy | Duration |
|------|:----------------:|:----------------:|:------------:|:--------:|
|   1  |              0.5 |             0.75 |         0.75 |   123.45 |
|   2  |             0.43 |             0.75 |         0.75 |   123.45 |
|   3  |              0.6 |              0.6 |          0.6 |      100 |  # submitted at Jan 1, 2020
|   4  |              0.6 |              0.6 |          0.6 |      100 |  # submitted at Jan 2, 2020
```
So we sort the submissions by the primary column, (Max Accuracy) and then by columns from left to right, so accuracy 1, then accuracy 2, then duration, then by submission_at.

## Submission rules

The submission rule set the behavior of the leaderboard regarding new submissions. Submissions can be forced to the leaderboard or manually selected, can be unique or multiple on the leaderboard, etc.

- **Add**: Only allow adding one submission
- **Add And Delete**: Allow users to add a single submission and remove that submission
- **Add And Delete Multiple**: Allow users to add multiple submissions and remove those submissions
- **Force Last**: Force only the last submission
- **Force Latest Multiple**: Force latest submission to be added to leaderboard (multiple)
- **Force Best**: Force only the best submission to the leaderboard

Here are the corresponding values for the YAML field `submission_rule`: "Add", "Add_And_Delete", "Add_And_Delete_Multiple", "Force_Last", "Force_Latest_Multiple" or "Force_Best".

## Hidden Leaderboard
If a leaderboard is marked as hidden, it will not be visible to participants in the competition. It will only be visible to platform administrators, competition administrators, and competition collaborators.

## Downloading Leaderboard Data
If an administrator, competition administrator, and competition collaborator would like to download the current leaderboard data, they will have access to a button labeled "CSV" on the leaderboard page. This creates a downloadable ZIP file. Each CSV file inside will be titled with the name of the leaderboard. The first row of the CSV is the title for each column, followed by all the submissions on the leaderboard.
This can be access directly through the API by sending a GET request to `[HOSTNAME]/api/competitions/'ID'/get_csv` where 'ID' is the competition ID.