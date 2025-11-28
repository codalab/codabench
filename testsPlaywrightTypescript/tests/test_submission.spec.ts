import { test, expect } from '@playwright/test';
// Disable Parralellism here because we only have one compute worker
//test.describe.configure({ mode: 'default' });

test('Test Submission on Newly created competition', async ({ page }) => {
  test.setTimeout(40_000)
  await page.goto('');
  await page.getByRole('link', { name: 'Benchmarks/Competitions' }).click();
  await page.getByRole('link', { name: 'Upload' }).click();
    let [competitionChooser] = await Promise.all([
        page.waitForEvent('filechooser'),
        page.getByRole('button', { name: '' }).click(),
    ]);
  await competitionChooser.setFiles([`test_files/competitions/competition.zip`]);
  await expect(page.locator('competition-upload')).toContainText('Competition created!');
  await page.getByRole('link', { name: 'View' }).click();
  await page.getByText('My Submissions').click();
  let [submissionChooser] = await Promise.all([
      page.waitForEvent('filechooser'),
      page.getByRole('button', { name: '' }).click(),
  ]);
  await submissionChooser.setFiles([`test_files/submissions/submission.zip`]);
  // Will wait for the progress bar to appear then dissapear before continuing
  await expect(page.locator('.ui.indicating')).toBeVisible();
  await expect(page.locator('.ui.indicating')).not.toBeVisible();
  await expect(async () => {
    await page.reload();
    await page.getByRole('cell', { name: 'Finished' }).first().waitFor({ state: 'visible', timeout: 3000 });
  }).toPass({
  // Probe, wait 1s, probe, wait 2s, probe, wait 10s, probe, wait 10s, probe
  // ... Defaults to [100, 250, 500, 1000].
  intervals: [1000],
  });
});

test('Test Submission: Iris v15 code', async ({ page }) => {
  test.setTimeout(40_000)
  await page.goto('');
  await page.getByRole('link', { name: 'Benchmarks/Competitions' }).click();
  await page.getByRole('link', { name: 'Upload' }).click();
    let [competitionChooser] = await Promise.all([
        page.waitForEvent('filechooser'),
        page.getByRole('button', { name: '' }).click(),
    ]);
  await competitionChooser.setFiles([`test_files/competitions/competition_15_iris.zip`]);
  await expect(page.locator('competition-upload')).toContainText('Competition created!');
  await page.getByRole('link', { name: 'View' }).click();
  await page.getByText('My Submissions').click();
  let [submissionChooser] = await Promise.all([
      page.waitForEvent('filechooser'),
      page.getByRole('button', { name: '' }).click(),
  ]);
  await submissionChooser.setFiles([`test_files/submissions/submission_15_iris_code.zip`]);
  // Will wait for the progress bar to appear then dissapear before continuing
  await expect(page.locator('.ui.indicating')).toBeVisible();
  await expect(page.locator('.ui.indicating')).not.toBeVisible();
  await expect(async () => {
    await page.reload();
    await page.getByRole('cell', { name: 'Finished' }).first().waitFor({ state: 'visible', timeout: 3000 });
  }).toPass({
  // Probe, wait 1s, probe, wait 2s, probe, wait 10s, probe, wait 10s, probe
  // ... Defaults to [100, 250, 500, 1000].
  intervals: [1000],
  });
});

test('Test Submission: Iris v15 result', async ({ page }) => {
  test.setTimeout(40_000)
  await page.goto('');
  await page.getByRole('link', { name: 'Benchmarks/Competitions' }).click();
  await page.getByRole('link', { name: 'Upload' }).click();
    let [competitionChooser] = await Promise.all([
        page.waitForEvent('filechooser'),
        page.getByRole('button', { name: '' }).click(),
    ]);
  await competitionChooser.setFiles([`test_files/competitions/competition_15_iris.zip`]);
  await expect(page.locator('competition-upload')).toContainText('Competition created!');
  await page.getByRole('link', { name: 'View' }).click();
  await page.getByText('My Submissions').click();
  let [submissionChooser] = await Promise.all([
      page.waitForEvent('filechooser'),
      page.getByRole('button', { name: '' }).click(),
  ]);
  await submissionChooser.setFiles([`test_files/submissions/submission_15_iris_result.zip`]);
  // Will wait for the progress bar to appear then dissapear before continuing
  await expect(page.locator('.ui.indicating')).toBeVisible();
  await expect(page.locator('.ui.indicating')).not.toBeVisible();
  await expect(async () => {
    await page.reload();
    await page.getByRole('cell', { name: 'Finished' }).first().waitFor({ state: 'visible', timeout: 3000 });
  }).toPass({
  // Probe, wait 1s, probe, wait 2s, probe, wait 10s, probe, wait 10s, probe
  // ... Defaults to [100, 250, 500, 1000].
  intervals: [1000],
  });
});

test('Test Submission: v15', async ({ page }) => {
  test.setTimeout(40_000)
  await page.goto('');
  await page.getByRole('link', { name: 'Benchmarks/Competitions' }).click();
  await page.getByRole('link', { name: 'Upload' }).click();
    let [competitionChooser] = await Promise.all([
        page.waitForEvent('filechooser'),
        page.getByRole('button', { name: '' }).click(),
    ]);
  await competitionChooser.setFiles([`test_files/competitions/competition_15.zip`]);
  await expect(page.locator('competition-upload')).toContainText('Competition created!');
  await page.getByRole('link', { name: 'View' }).click();
  await page.getByText('My Submissions').click();
  let [submissionChooser] = await Promise.all([
      page.waitForEvent('filechooser'),
      page.getByRole('button', { name: '' }).click(),
  ]);
  await submissionChooser.setFiles([`test_files/submissions/submission_15.zip`]);
  // Will wait for the progress bar to appear then dissapear before continuing
  await expect(page.locator('.ui.indicating')).toBeVisible();
  await expect(page.locator('.ui.indicating')).not.toBeVisible();
  await expect(async () => {
    await page.reload();
    await page.getByRole('cell', { name: 'Finished' }).first().waitFor({ state: 'visible', timeout: 3000 });
  }).toPass({
  // Probe, wait 1s, probe, wait 2s, probe, wait 10s, probe, wait 10s, probe
  // ... Defaults to [100, 250, 500, 1000].
  intervals: [1000],
  });
});

test('Test Submission: v18', async ({ page }) => {
  test.setTimeout(40_000)
  await page.goto('');
  await page.getByRole('link', { name: 'Benchmarks/Competitions' }).click();
  await page.getByRole('link', { name: 'Upload' }).click();
    let [competitionChooser] = await Promise.all([
        page.waitForEvent('filechooser'),
        page.getByRole('button', { name: '' }).click(),
    ]);
  await competitionChooser.setFiles([`test_files/competitions/competition_18.zip`]);
  await expect(page.locator('competition-upload')).toContainText('Competition created!');
  await page.getByRole('link', { name: 'View' }).click();
  await page.getByText('My Submissions').click();
  let [submissionChooser] = await Promise.all([
      page.waitForEvent('filechooser'),
      page.getByRole('button', { name: '' }).click(),
  ]);
  await submissionChooser.setFiles([`test_files/submissions/submission_18.zip`]);
  // Will wait for the progress bar to appear then dissapear before continuing
  await expect(page.locator('.ui.indicating')).toBeVisible();
  await expect(page.locator('.ui.indicating')).not.toBeVisible();
  await expect(async () => {
    await page.reload();
    await page.getByRole('cell', { name: 'Finished' }).first().waitFor({ state: 'visible', timeout: 3000 });
  }).toPass({
  // Probe, wait 1s, probe, wait 2s, probe, wait 10s, probe, wait 10s, probe
  // ... Defaults to [100, 250, 500, 1000].
  intervals: [1000],
  });
});

test('Test Submission: v2 multi task fact sheet', async ({ page }) => {
  // Higher timeout because there are multiple tasks per submission
  test.setTimeout(120_000)
  await page.goto('');
  await page.getByRole('link', { name: 'Benchmarks/Competitions' }).click();
  await page.getByRole('link', { name: 'Upload' }).click();
    let [competitionChooser] = await Promise.all([
        page.waitForEvent('filechooser'),
        page.getByRole('button', { name: '' }).click(),
    ]);
  await competitionChooser.setFiles([`test_files/competitions/competition_v2_multi_task_fact_sheet.zip`]);
  await expect(page.locator('competition-upload')).toContainText('Competition created!');
  await page.getByRole('link', { name: 'View' }).click();
  await page.getByText('My Submissions').click();
  await page.locator('input[name="text"]').click();
  await page.locator('input[name="text"]').fill('test');
  await page.locator('select[name="selection"]').selectOption('v3');
  await page.locator('input[name="text_required"]').click();
  await page.locator('input[name="text_required"]').fill('test');
  let [submissionChooser] = await Promise.all([
      page.waitForEvent('filechooser'),
      page.getByRole('button', { name: '' }).click(),
  ]);
  await submissionChooser.setFiles([`test_files/submissions/submission.zip`]);
  // Will wait for the progress bar to appear then dissapear before continuing
  await expect(page.locator('.ui.indicating')).toBeVisible();
  await expect(page.locator('.ui.indicating')).not.toBeVisible();
  await expect(async () => {
    await page.reload();
    await page.getByRole('cell', { name: 'Finished' }).first().waitFor({ state: 'visible', timeout: 3000 });
  }).toPass({
  // Probe, wait 1s, probe, wait 2s, probe, wait 10s, probe, wait 10s, probe
  // ... Defaults to [100, 250, 500, 1000].
  intervals: [1000],
  });
});

test('Test Submission: v2 multi task', async ({ page }) => {
  // Higher timeout because there are multiple tasks per submission
  test.setTimeout(120_000)
  await page.goto('');
  await page.getByRole('link', { name: 'Benchmarks/Competitions' }).click();
  await page.getByRole('link', { name: 'Upload' }).click();
    let [competitionChooser] = await Promise.all([
        page.waitForEvent('filechooser'),
        page.getByRole('button', { name: '' }).click(),
    ]);
  await competitionChooser.setFiles([`test_files/competitions/competition_v2_multi_task.zip`]);
  await expect(page.locator('competition-upload')).toContainText('Competition created!');
  await page.getByRole('link', { name: 'View' }).click();
  await page.getByText('My Submissions').click();
  let [submissionChooser] = await Promise.all([
      page.waitForEvent('filechooser'),
      page.getByRole('button', { name: '' }).click(),
  ]);
  await submissionChooser.setFiles([`test_files/submissions/submission.zip`]);
  // Will wait for the progress bar to appear then dissapear before continuing
  await expect(page.locator('.ui.indicating')).toBeVisible();
  await expect(page.locator('.ui.indicating')).not.toBeVisible();
  await expect(async () => {
    await page.reload();
    await page.getByRole('cell', { name: 'Finished' }).first().waitFor({ state: 'visible', timeout: 3000 });
  }).toPass({
  // Probe, wait 1s, probe, wait 2s, probe, wait 10s, probe, wait 10s, probe
  // ... Defaults to [100, 250, 500, 1000].
  intervals: [1000],
  });
});