
This is our use case of cancer benchmarks.
This document focuses on how to run the following three bundles in Codabench

- `CODABENCH CANCER HETEROGENEITY DT#1 TRANSCRIPTOME PANCREAS`
- `CODABENCH CANCER HETEROGENEITY DT#2 METHYLOME PANCREAS`
- `CODABENCH CANCER HETEROGENEITY DT#3 IMMUNE CELL TYPES`

## Steps
### 1. Decompressing the original bundle
![image](../../_attachments/102427038-7aafd280-404b-11eb-94a5-9df0dcac3901_17528513125646255.png)

Unzip the bundle from its original zip file format into a folder.

### 2. Decompressing ingestion_program_1.zip
![image](../../_attachments/102427080-8c917580-404b-11eb-8f2c-be74be778fb4_17528513126002839.png)

### 3. Modify the sub_ingestion.R file in the ingestion_program_1 folder.
![image](../../_attachments/102427100-9a46fb00-404b-11eb-9068-1437e4f5352a_17528513126199927.png)

Add lines 19 and 20 of code, and replace the underlined variable in line 25 with submission_program_dir

Two new lines of code have been added to allow the v2 compute worker to find the user-submitted program (program.R). (Because the v2 compute worker does not support searching for user-submitted code in subfolders.)

```r
child_dir <- list.files(path=submission_program)
submission_program_dir <- paste0(submission_program, .Platform$file.sep, tail(child_dir, n=1))
```
```r
// read code submitted by the participants :
.tempEnv <- new.env( )
source(
    file  = paste0(submission_program_dir, .Platform$file.sep, "program.R")
  , local = .tempEnv
)
```
![image](../../_attachments/102427341-193c3380-404c-11eb-9a69-5a024d3a6599_17528513130877678.png)

### 4.Save the changes and re-zip the ingestion_program_1 folder.
Open the command line and go to the ingestion_program_1 folder.

![image](../../_attachments/102427380-2d803080-404c-11eb-9161-2c8d5fb09369_17528513126502273.png)

Use the following command to package the modified folder as a zip file
`zip -r ingestion_program_1.zip *`

![image](../../_attachments/102427403-3bce4c80-404c-11eb-9cc8-e241fd4e7474_17528513126719942.png)

Replace the latest compressed ingestion_program_1.zip file with the previous ingestion_program_1.zip file, and delete the ingestion_program_1 folder.

![image](../../_attachments/102427413-45f04b00-404c-11eb-8b4c-c6e8b64fd945_17528513131024394.png)

### 5. Recompress the modified original bundle.
Go to the directory at the same level as `competition.yaml` and execute the following command to compress the file
`zip -r Codabench_cancer_heterogeneity_DT#2.zip *`

![image](../../_attachments/102427457-5bfe0b80-404c-11eb-8c52-ffe5362b54e1_17528513131442835.png)

### 6. Creating competition with compressed bundles
### 7. Modify the default execution time
The default execution time is 10 minutes, but since these three bundles are time-consuming to execute, you have to turn it up.

![image](../../_attachments/102427495-70420880-404c-11eb-8864-443b5f3d1913_17528513127302663.png)
![image](../../_attachments/102427510-7932da00-404c-11eb-8138-63889a0664b3_17528513127678237.png)
![image](../../_attachments/102427536-818b1500-404c-11eb-9ab5-83ed190db742_17528513128221796.png)

We recommend that you adjust the time to the maximum value of `2147483647`, so that the task will not time out and be forced to terminate by the compute worker.


## Summary
This paragraph summarizes the results of the execution of three bundles in codalab v2.
### CODABENCH CANCER HETEROGENEITY DT#1 TRANSCRIPTOME PANCREAS
[https://www.codabench.org/competitions/147/](https://www.codabench.org/competitions/147/)

All three submissions were successful.

![image](../../_attachments/102427661-ca42ce00-404c-11eb-93c8-df58812c4085_1752851312901565.png)

### CODABENCH CANCER HETEROGENEITY DT#2 METHYLOME PANCREAS
[https://www.codabench.org/competitions/174/](https://www.codabench.org/competitions/174/)

Two Submissions were successfully run, while the third failed due to insufficient execution time (We have now adjusted from the original 10,000 minute execution time limit to a maximum of 2,147483647.)

![image](../../_attachments/102427705-dfb7f800-404c-11eb-87c1-c4ac69c003be_1752851312950296.png)

### CODABENCH CANCER HETEROGENEITY DT#3 IMMUNE CELL TYPES
[https://www.codabench.org/competitions/148/](https://www.codabench.org/competitions/148/)

2 Submissions run successfully, 1 execution fails (screenshot below)

![image](../../_attachments/102427767-f5c5b880-404c-11eb-9caa-f0cd7a702a84_17528513130498507.png)

Failed execution screenshot:

![image](../../_attachments/102427791-0118e400-404d-11eb-923a-87d724ff5a54_1752851313121837.png)