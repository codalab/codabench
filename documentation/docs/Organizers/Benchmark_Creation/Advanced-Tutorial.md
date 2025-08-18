
Here is an advanced tutorial. If you are new to CodaBench, please refer to [get started tutorial](Getting-started-with-Codabench.md) first.
In this article, you'll learn how to use more advanced features and how to create benchmarks using either the editor or bundles.
Before proceeding to our tutorial, make sure you have registered for an account on the [Codabench](https://www.codabench.org/) website.

The image below is an overview of the benchmark creation process
![image](../../_attachments/102429234-771d4b00-404d-11eb-9ec3-bc75d39d3194_17528513092407322.png)

## Creating a Benchmark by Editor

In this chapter, I'll take you step by step through the Editor's approach to creating benchmark, including algorithm type and dataset type.

### Step 1: Click on Management in the top right corner of Codabench's home page under Competitions.
![image](../../_attachments/102429989-a9c74380-404d-11eb-8b99-9e7829fe8678_17528513092920961.png)
When you click on it, you will see the screen as shown in the screenshot below.
![image](../../_attachments/102430225-b9468c80-404d-11eb-81f1-879138afad2c_175285130932125.png)

### Step 2: Click on the Create button in the top right corner of Competition Management.
![image](../../_attachments/102430591-d24f3d80-404d-11eb-8adf-1f562d2f9cb4_17528513093284764.png)

### Step 3: Fill in the Details tab content.

![image](../../_attachments/102431578-12aebb80-404e-11eb-8d07-d74e9de46280_17528513097437637.png)

### Step 4: Fill in the Participant Tab.

![image](../../_attachments/102431721-1d695080-404e-11eb-87a4-92a4b43b349c_1752851309399166.png)

### Step 5: Fill in the Pages Tab.

![image](../../_attachments/102431937-2c500300-404e-11eb-9a28-344f26d79013_17528513093988035.png)

### Step 6: Fill in the Phases Tab.

![image](../../_attachments/102432087-36720180-404e-11eb-9dda-a593d7a45af2_17528513094299598.png)

![image](../../_attachments/102432234-40940000-404e-11eb-8a3d-1e72b2688267_17528513094664094.png)

When you click on the Manage Tasks/Datasets button, you will see the screenshot shown below

Click the Add Dataset button in the diagram to upload the resource files needed to create the competition.

![image](../../_attachments/102432435-4d185880-404e-11eb-967f-1735f6a9f145_17528513094839308.png)

Creating a phase will require a bundle of the following types (.zip format), I'll give you more details on how to write these bundle later.

Now you just need to have this concept in your mind

![image](../../_attachments/102432573-56092a00-404e-11eb-9788-512586edd693_1752851309496168.png)

Here are the screenshots of the 5 types of bundles after they were uploaded

![image](../../_attachments/102432684-5e616500-404e-11eb-8b82-8ea332050cdf_17528513095790792.png)

![image](../../_attachments/102432819-67523680-404e-11eb-9032-b725058ffa3c_17528513102032712.png)

![image](../../_attachments/102432974-71743500-404e-11eb-95ef-84d39597a412_1752851309572427.png)

![image](../../_attachments/102433142-7b963380-404e-11eb-9ad0-035eb60d7f64_17528513096323566.png)

### Step 7: Fill in the Leaderboard Tab.

![image](../../_attachments/102433276-84870500-404e-11eb-8638-60eeab21fe8d_17528513096378942.png)

![image](../../_attachments/102433391-8c46a980-404e-11eb-871c-6d443be44062_1752851309654381.png)

### Step 8: Save and Publish the Benchmark

![image](../../_attachments/102433537-95377b00-404e-11eb-8649-57f70a830564_1752851309686341.png)

![image](../../_attachments/102433657-9cf71f80-404e-11eb-9aa0-d23cf595c7db_1752851309773052.png)



## Creating a Benchmark by Bundle

Creating a benchmark through bundles is a much more efficient way than using editors.

### Simple Version Example: CLASSIFY WHEAT SEEDS

### Step 1: Download bundle

https://github.com/codalab/competition-examples/blob/master/codabench/wheat_seeds/code_submission_bundle.zip

Click on the link above to download the bundle in the screenshot.

![image](../../_attachments/102433828-aa140e80-404e-11eb-9886-3f6960eb6a5e_17528513100792131.png)


### Step 2: Go to the benchmark upload page

![image](../../_attachments/102433943-b1d3b300-404e-11eb-9594-39de8566c6a0_17528513097862737.png)

![image](../../_attachments/102433960-bbf5b180-404e-11eb-8102-26c03d5084b8_17528513098046653.png)

![image](../../_attachments/102433974-c57f1980-404e-11eb-9b50-54b170755850_17528513098181317.png)


### Step 3: Upload the bundle

After the bundle has been uploaded, you will see the screenshot shown below.

![image](../../_attachments/102433995-ce6feb00-404e-11eb-95c9-2ed9e5d8bb54_1752851309822554.png)


### Step 4: View your new benchmark

![image](../../_attachments/102434012-d6c82600-404e-11eb-85dd-88338d7aa033_17528513098401737.png)

![image](../../_attachments/102434028-e182bb00-404e-11eb-9de8-002e4589db66_17528513099222646.png)



## Benchmark Examples

Example bundles for code & dataset competition can be found here:

https://github.com/codalab/competition-examples/tree/master/codabench

### Iris

[Iris Codabench Bundle](https://github.com/codalab/competition-examples/tree/master/codabench/iris) is a simple benchmark involving two phases, code submission and results submission.

### AutoWSL

Two versions of the [Automated Weakly Supervised Learning Benchmark](https://github.com/codalab/competition-examples/tree/master/codabench/autowsl):
- [Code submission benchmark](https://github.com/codalab/competition-examples/tree/master/codabench/autowsl/code_submission)
- [Dataset submission benchmark](https://github.com/codalab/competition-examples/tree/master/codabench/autowsl/dataset_submission)

### Mini-AutoML

[Mini-AutoML Bundle](https://github.com/codalab/competition-examples/tree/master/codabench/mini-automl) is a benchmark template for Codabench, featuring code submission to multiple datasets (tasks).


## How do I set up submission comments for multiple submissions?

### Steps

#### Step 1: Click the edit button

![image](../../_attachments/102434058-f5c6b800-404e-11eb-98e2-88ee12195d7a_17528513098936615.png)


#### Step 2: Enable multiple submissions on leaderboard

![image](../../_attachments/102434073-fcedc600-404e-11eb-859c-658fdc57bb37_17528513098851938.png)

![image](../../_attachments/102434089-04ad6a80-404f-11eb-9f70-faa80fa8b6ba_17528513099604332.png)

#### Step 3: Set up submission comment

![image](../../_attachments/102434105-0e36d280-404f-11eb-99b1-dae0127cb941_1752851309982288.png)

#### Step 4: Save all changes

![image](../../_attachments/102434120-168f0d80-404f-11eb-91e1-04f52a7dd77a_1752851309963938.png)

#### Step 5: Leave a comment before making submission

![image](../../_attachments/102434132-1d1d8500-404f-11eb-8370-11fe623f3d2f_17528513103749812.png)

#### Step 6: Check out the leaderboard

![image](../../_attachments/102434153-27d81a00-404f-11eb-9aea-86763cc0d631_17528513100395033.png)
