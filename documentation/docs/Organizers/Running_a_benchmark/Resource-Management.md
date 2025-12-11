This page is where you can manage your resources e.g. Submissions, Datasets, Programs, Tasks, and Competition Bundles. You can also view and manage your quota on this page.


You can access this interface by clicking on "**Resources**" in the main menu:
![](_attachments/7013c755-824f-4c12-9c69-ef8ef03025eb_17534367071670744.jpg)


---

## Submissions 
In this tab, you can view all your submissions either uploaded in this interface or submitted to a competition.
![](_attachments/3eb6336a-5f0c-4abc-abd2-a9c4280b0863_17534367073499072.jpg)

By clicking the `Add Submission` button you can fill a form and attach a submission file to upload a new submission. This is useful in different cases e.g. when you want to share a sample submission with the participants of a competition you are organizing.
![](_attachments/fb6ecce8-fdc8-4fff-af33-ad68153ded86_17534367075859904.jpg)


## Datasets/Programs
In this tab,  you can view the datasets and programs that you have uploaded. You can also view auto-created and publicly available datasets/programs by checking the relevant checkboxes. 

![](_attachments/548b326e-5e1b-4688-82c2-fed0a402af21_17534367080187995.jpg)

By clicking the `Add Dataset/Program` button you can fill a form and attach a dataset file to upload.

![](_attachments/b7aba5b0-1eab-4b8c-8f0e-7d463aa20c3b_1753436707984425.jpg)

You can click on a dataset/program and make it public or private. This is useful when you want to share a dataset with participants so that hey can use it to prepare a submission for a competition.

![](_attachments/99ec6090-86bd-4425-8f12-46115e09409d_1753436708048147.jpg)


For a general breakdown of the roles of different types of datasets, see this link: [Competition Bundle Structure: Data types and their role](https://docs.codabench.org/latest/Organizers/Benchmark_Creation/Competition-Bundle-Structure/#data-types-and-their-role).



## Tasks
In this tab, you can manage your tasks. You can create a new task, upload a task, edit a task and check task details.
![](_attachments/fe61c496-4b40-4c6e-bda1-bfa579393987_17534367082532165.jpg)


### Create New Task
To create a new task, you have to fill the form by entering task name and description
![](_attachments/7217bebc-0a9c-45f4-b0e6-2881c8e74a67_1753436708407207.jpg)

You also have to select datasets and programs from the already uploaded ones in the Datasets/Programs tab
![](_attachments/b99658f9-4819-49b2-a272-69503a4361ac_17534367088250148.jpg)



### Edit a Task
You can change the task name and description 
![](_attachments/49fe8121-9cd5-4364-ac5f-f463396ea525_1753436708800273.jpg)

You can also change the datasets/programs used in the task
![](_attachments/b89268e3-bbdd-483c-a595-add9eb5fee7a_17534367089431207.jpg)

!!! note
    Organizers should be careful when updating a task because some submissions may have used the task and updating the task will not allow you to rerun those submissions because the task they have used is now changed.



### Upload a Task
You can create a new task by uploading a task zip that has the required files in the correct format.
![](_attachments/1ffc7805-950e-46ad-adfe-bca8a4b85c70_1753436708942981.jpg)


Create a zip file that consists of a `task.yaml` file and zips of datasets/programs if required. You can use already existing datasets/prograsm by using their keys in the yaml, or upload new datasets/programs or use a mix of keys and files e.g. you choose to use already existing input data and reference data but use zip files for ingestion and scoring program. In the last case, codabench will create two programs and then use them in your task and will use existing datasets in the same task.

Check the files below for examples of task upload zips.

- [task_with_keys_only.zip](https://github.com/user-attachments/files/17597251/task_with_keys_only.zip)
- [task_with_files_only.zip](https://github.com/user-attachments/files/17597252/task_with_files_only.zip)
- [task_with_mix_of_keys_and_files.zip](https://github.com/user-attachments/files/17597265/task_with_mix_of_keys_and_files.zip)

For reference, here is the content of the `task.yaml` file that you can find inside the `task_with_mix_of_keys_and_files.zip` task:
```yaml title="task.yaml"
name: Iris Task
description: Iris Task for Flower classification
is_public: false
scoring_program:
  zip: iris-scoring-program.zip
ingestion_program:
  zip: iris-ingestion-program.zip
input_data:
  key: 6c3e6dde-d0fa-4c22-af66-030187dbfd4f
reference_data:
  key: c4179c3f-498c-486a-8ac5-1e194036a3ed
```


### Task Details
In the task details, you can view all the task details e.g. title, description, task owner, created date, people with whom this task is shared, competitions where this task is used, the datasets/programs used in this task and option to download them, and option to make the task public/private.
![](_attachments/996bf4c7-bccf-44b3-b90d-7513f8d83c0f_17534367093325448.jpg)





## Competition Bundles
In this tab, you can mange your competition bundles. These bundles are stored when you create your competitions using a zip. 
![](_attachments/b6c7f500-f531-4b1c-9b08-86609c197126_17534367096771557.jpg)



## Quota and Cleanup
This section of the resource interface shows you the usage of your quota. A free quota of 15 GB is given to all the users and this can be increased by the platform administrators in special circumstances for selected users. You can also do some quick cleanup from here by deleting unused resources e.g. submissions, datasets and tasks etc.
![](_attachments/e4bcf27a-6af1-4b1a-9802-1af259570619_1753436709645197.jpg)


