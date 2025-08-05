In this page, you'll learn how to update critical elements of your benchmark like the scoring program or the reference data, while your benchmark is already up and running.

For a general overview of resources management, [click here](Resource-Management.md).

If order to update your programs or data, you have two approaches:
- **A.** Edit an existing Task (simpler and straightforward)
- **B.** Create a new Task

Let's see both approach in detail.

## A. Edit an existing Task

### 1. Prepare the new dataset or program

- Make local changes to the elements you want to update: scoring program, ingestion program, input data and/or reference data.

- Zip the new version of your program or data. **Make sure to zip the files at the root of the archive, without zipping the folder structure.**

### 2. Upload the new dataset or program 

- Go to Resources

![](_attachments/c3679b14-444f-4718-ae4a-ac0d5f297b76_17534367051868246.jpg)

- Go to "Datasets and Programs" and click on "Add Dataset/Program"

![](_attachments/879ae590-498b-49cf-9872-77c15e4b5dae_17534367054113083.jpg)

- Fill in the form: Name the new program or dataset, select the type (scoring program, input data, etc.), and select your ZIP file

![](_attachments/3f1dc4a3-f90d-4497-abce-ff3b8960278f_17534367055954835.jpg)

### 3. Update the Task used by your benchmark

Still on "Resources" page, go to the "Task" tab. Find the task you want to edit. In order to recognize it, make sure it is marked as "In Use", and click to see more information and make sure it is related to the right benchmark.

Then click on the pencil symbol to edit it:
![](_attachments/25b506f9-dc9b-4ffc-8c2a-8c8bb95b3149_17534367056648443.jpg)

Start typing the name of your new program or dataset in the corresponding field and select it, then save.

![](_attachments/377c4f6b-8975-4462-91c0-e5c9926b91f6_17534367061268125.jpg)


**Done!** Your task is updated and its new version will be triggered by new submissions. You don't need to update the benchmark/competition for the change to take effect.


## B. Create a new Task

### 1. Prepare your new dataset / program

First, upload the new versions of your program and/or dataset. To that end, follow steps **1.** and **2.** presented above.

### 2. Create Task

- Go to "Resources" > "Task" > "Create Task"

![](_attachments/78d98652-2ad6-47a2-90e1-96700325a4a4_1753436706098669.jpg)

- Fill in all fields: Name, Description, Scoring program, (optionally: Ingestion program, Reference data, Input data)

### Edit your benchmark

- Once your task is created, go to the editor of your challenge

![](_attachments/49650ec6-ce8f-440b-9245-0ff04dcfb7df_17534367060782135.jpg)

- Go to "Phases" and edit the relevant phase

![](_attachments/f136dce0-2be2-42d4-9d27-9743149f1a4f_1753436706408659.jpg)

- Select your new task and save

![](_attachments/aba614a8-06f5-4c81-b060-0afc3647e777_17534367063286426.jpg)

**Done!** Your benchmark is now ready to run your new task for future submissions.
