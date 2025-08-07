!!! warning
    You need to stop the database from being changed while running these commands.
    They might take time to complete depending on the size of your database.


Start maintenance mode:
```sh
touch maintenance/maintenance.on
```

### 1. Django migration ([1774](https://github.com/codalab/codabench/pull/1774), [1752](https://github.com/codalab/codabench/pull/1752))

```sh
docker compose exec django ./manage.py migrate
```

### 2. Reset User Quota from Bytes to GB ([1749](https://github.com/codalab/codabench/pull/1749)) 

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


### 3. Important for file sizes cleanup ([1752](https://github.com/codalab/codabench/pull/1752)) 

We have some critical changes here so before deployment we should run the following 3 blocks of code to get the last ids of `Data`, `Submission` and `SubmissionDetail`

Then, in the shell_plus:

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

After we have the latest ids, we should deploy and run the 3 blocks of code below to fix the sizes i.e. to convert all kib to bytes to make everything consistent. For new files uploaded after the deployment, the sizes will be saved in bytes automatically that is why we need to run the following code for older files only.

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
rm maintenance/maintenance.on
```
