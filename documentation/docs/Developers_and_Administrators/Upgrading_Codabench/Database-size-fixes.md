!!! warning
    You need to stop the database from being changed while running these commands, so keep maintenance mode on from the start of the upgrade until the end of these steps.
    They might take time to complete depending on the size of your database.

### 1. Before the upgrade: get the last IDs ([1752](https://github.com/codalab/codabench/pull/1752))

File sizes are now saved in bytes instead of KiB. Before running `git pull` in the standard upgrade commands (but after turning on maintenance mode), get the last ids of `Data`, `Submission` and `SubmissionDetail`. Only the files up to these ids will be converted.

```sh
docker compose exec django ./manage.py shell_plus
```

```python
# Get the maximum ID for Data
from datasets.models import Data
latest_id_data = Data.objects.latest('id').id
print("Data Last ID: ", latest_id_data)
```

```python
# Get the maximum ID for Submission
from competitions.models import Submission
latest_id_submission = Submission.objects.latest('id').id
print("Submission Last ID: ", latest_id_submission)
```

```python
# Get the maximum ID for Submission Detail
from competitions.models import SubmissionDetails
latest_id_submission_detail = SubmissionDetails.objects.latest('id').id
print("SubmissionDetail Last ID: ", latest_id_submission_detail)
```

### 2. Upgrade

Run the standard upgrade commands, but do not remove maintenance mode yet.

### 3. Reset User Quota from Bytes to GB ([1749](https://github.com/codalab/codabench/pull/1749))

```sh
docker compose exec django ./manage.py shell_plus
```

```python
from profiles.quota import reset_all_users_quota_to_gb
reset_all_users_quota_to_gb()
```

```python
# Convert all 16 GB quota into 15 GB
from profiles.models import User
users = User.objects.all()
for user in users:
    # Reset quota to 15 if quota is between 15 and 20
    # Do not reset quota for special users like adrien
    if user.quota > 15 and user.quota < 20:
        user.quota = 15
        user.save()
```


### 4. Convert the file sizes of older files ([1752](https://github.com/codalab/codabench/pull/1752))

In a new shell_plus, set `latest_id_data`, `latest_id_submission` and `latest_id_submission_detail` to the ids printed in step 1 (for example `latest_id_data = 1234`), then run the 3 blocks of code below to convert all KiB to bytes. New files uploaded after the upgrade are saved in bytes automatically, which is why this conversion is only for older files.

```python
# Run the conversion only for records with id <= latest_id
from datasets.models import Data
for data in Data.objects.filter(id__lte=latest_id_data):
    if data.file_size:
        data.file_size = data.file_size * 1024  # Convert from KiB to bytes
        data.save()
```

```python
# Run the conversion only for records with id <= latest_id
from competitions.models import Submission
for sub in Submission.objects.filter(id__lte=latest_id_submission):
    updated = False  # Track if any field is updated

    if sub.prediction_result_file_size:
        sub.prediction_result_file_size = sub.prediction_result_file_size * 1024  # Convert from KiB to bytes
        updated = True
    
    if sub.scoring_result_file_size:
        sub.scoring_result_file_size = sub.scoring_result_file_size * 1024  # Convert from KiB to bytes
        updated = True

    if sub.detailed_result_file_size:
        sub.detailed_result_file_size = sub.detailed_result_file_size * 1024  # Convert from KiB to bytes
        updated = True
    
    if updated:
        sub.save()
```

```python
# Run the conversion only for records with id <= latest_id
from competitions.models import SubmissionDetails
for sub_det in SubmissionDetails.objects.filter(id__lte=latest_id_submission_detail):
    if sub_det.file_size:
        sub_det.file_size = sub_det.file_size * 1024  # Convert from KiB to bytes
        sub_det.save()
```

Then, do not forget to stop maintenance mode:

```sh
rm maintenance_mode/maintenance.on
```
