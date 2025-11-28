import { test, expect } from '@playwright/test';

test('Test Competition Upload', async ({ page }) => {
    await page.goto('');
    await page.getByRole('link', { name: 'Benchmarks/Competitions' }).click();
    await page.getByRole('link', { name: 'Upload' }).click();
    let [competitionChooser] = await Promise.all([
        page.waitForEvent('filechooser'),
        page.getByRole('button', { name: '' }).click(),
    ]);
    await competitionChooser.setFiles([`test_files/iris_code/iris3.zip`]);
    await expect(page.locator('competition-upload')).toContainText('Competition created!');
});


test('Test Task Creation', async ({ page }) => {
    await page.goto('');
    await page.locator('i').nth(5).click();
    await page.getByRole('link', { name: 'Resources' }).click();
    await page.getByText('Datasets and programs').first().click();
    // No need to create the task if it already exists
    await page.getByRole('textbox', { name: 'Search...' }).click();
    await page.getByRole('textbox', { name: 'Search...' }).fill('Test Scoring Program');
    if (await page.getByRole('cell', { name: 'Test Scoring Program' }).isVisible()) {
    }
    else {
        await page.getByRole('button', { name: 'Add Dataset/Program' }).click();
        await page.getByRole('textbox', { name: 'Name' }).fill('Test Scoring Program');
        await page.getByRole('textbox', { name: 'Description' }).click();
        await page.getByRole('textbox', { name: 'Description' }).fill('Test Scoring Program');
        // If we await this, the dropdown will close, playwright won't be able to chose the scoring program
        page.locator('.field > .ui > .dropdown').click();
        await page.getByText('Scoring Program', { exact: true }).nth(5).click();
        let [scoringProgramChoose] = await Promise.all([
            page.waitForEvent('filechooser'),
            page.getByRole('button', { name: '' }).click(),
        ]);
        await scoringProgramChoose.setFiles([`test_files/Task/Scoring Program/scoring_program.zip`]);
        await page.getByRole('button', { name: ' Upload' }).click();
        await page.getByText('Tasks', { exact: true }).click();
        await page.getByText('Create Task').first().click();
        await page.getByRole('textbox', { name: 'Name', exact: true }).click();
        await page.getByRole('textbox', { name: 'Name', exact: true }).fill('');
        await page.getByRole('textbox', { name: 'Name', exact: true }).click();
        await page.getByRole('textbox', { name: 'Name', exact: true }).fill('Playwright Test Task');
        await page.getByRole('textbox', { name: 'Description' }).click();
        await page.getByRole('textbox', { name: 'Description' }).fill('Test Task Description');
        await page.getByText('Datasets and programs').nth(3).click();
        await page.locator('#scoring_program').click();
        await page.locator('#scoring_program').fill('test');
        await page.locator('a').filter({ hasText: 'Test Scoring ProgramTest' }).click();
        await page.getByText('Create', { exact: true }).click();
    }
});

test('Test Manual Competition Creation', async ({ page }) => {
    await page.goto('');
    await page.getByRole('link', { name: 'Benchmarks/Competitions' }).click();
    await page.getByRole('link', { name: 'Create' }).click();
    await page.getByRole('textbox').nth(1).click();
    await page.getByRole('textbox').nth(1).fill('Test Title');
    await page.locator('.CodeMirror').first().click();
    await page.getByRole('application').getByRole('textbox').fill('Test Description');
    await page.getByRole('textbox', { name: 'Example: codalab/codalab-' }).click();
    await page.getByRole('textbox', { name: 'Example: codalab/codalab-' }).fill('codalab/codalab-legacy:py37');
    await page.getByRole('textbox', { name: 'Example: $1000 for the top' }).click();
    await page.getByRole('textbox', { name: 'Example: $1000 for the top' }).fill('100€ for the Top Participant');
    await page.getByRole('textbox', { name: 'Example: email@example.com' }).click();
    await page.getByRole('textbox', { name: 'Example: email@example.com' }).fill('test@email.com');
    let [competitionChooser] = await Promise.all([
        page.waitForEvent('filechooser'),
        page.getByRole('button', { name: '' }).click(),
    ]);
    await competitionChooser.setFiles([`test_files/competition/test_logo.png`]);
    await page.getByText('Enable Competition Forum').click();
    await page.getByText('Auto-run submissions').click();
    await page.getByText('Participation').click();
    await page.locator('.field.required > .EasyMDEContainer > .CodeMirror').first().click();
    await page.getByRole('application').filter({ hasText: '|||xxxxxxxxxx 101:' }).getByRole('textbox').fill('Terms and Conditions');
    await page.locator('input[name="registration_auto_approve"]').check();
    await page.locator('a').filter({ hasText: 'Pages' }).click();
    await page.getByRole('button', { name: ' Add page' }).click();
    await page.getByRole('textbox').nth(1).click();
    await page.getByRole('textbox').nth(1).fill('Page 1');
    await page.locator('div:nth-child(2) > .EasyMDEContainer > .CodeMirror > .CodeMirror-scroll > .CodeMirror-sizer > div > .CodeMirror-lines > div > .CodeMirror-code > .CodeMirror-line').click();
    await page.getByRole('application').getByRole('textbox').fill('This is a page');
    await page.getByText('Save').nth(1).click();
    await page.locator('a').filter({ hasText: 'Phases' }).click();
    await page.getByRole('button', { name: ' Add phase' }).click();
    await page.locator('input[name="name"]').click();
    await page.locator('input[name="name"]').fill('Phase 1');
    await page.locator('input[name="start_date"]').click();
    await page.getByRole('cell', { name: '15' }).click();
    await page.locator('input[name="start_time"]').click();
    await page.getByRole('cell', { name: '14:' }).click();
    await page.getByRole('cell', { name: '14:00' }).click();
    await page.locator('.ui.search.selection.dropdown.multiple').first().click();
    await page.locator('.ui.search.selection.dropdown.multiple > .search').first().fill('Playwright ');
    await page.getByText('Playwright Test Task').first().click();
    await page.getByText('Advanced').click();
    await page.locator('input[name="max_submissions_per_day"]').click();
    await page.locator('input[name="max_submissions_per_day"]').fill('10');
    await page.locator('input[name="max_submissions_per_person"]').click();
    await page.locator('input[name="max_submissions_per_person"]').fill('100');
    await page.getByText('Save').nth(3).click();
    await page.getByText('Leaderboard', { exact: true }).click();
    await page.getByRole('button', { name: ' Add leaderboard' }).click();
    await page.locator('input[name="title"]').click();
    await page.locator('input[name="title"]').fill('LeaderBoardTitle');
    await page.locator('input[name="key"]').click();
    await page.locator('input[name="key"]').fill('Key');
    await page.getByText('Add column').click();
    await page.locator('input[name="column_key_0"]').click();
    await page.locator('input[name="column_key_0"]').fill('Colomn Keyssss');
    await page.getByRole('spinbutton').click();
    await page.getByRole('spinbutton').fill('3');
    await page.getByText('Save').nth(4).click();
    await page.getByRole('button', { name: 'Save' }).click();
    
    // Now we verify some of the information we entered previously
    await expect(page.locator('.reward-container')).toBeVisible();
    await expect(page.locator('comp-detail-header')).toContainText('100€ for the Top Participant');
    await expect(page.locator('#page_0')).toContainText('This is a page');
    await page.getByText('Terms', { exact: true }).click();
    await expect(page.locator('#page_term')).toContainText('Terms and Conditions');
    await page.getByText('Phases').click();
    await expect(page.locator('comp-tabs')).toContainText('Phase 1');
    await expect(page.locator('comp-detail-header')).toContainText('test@email.com');
    await page.getByText('Results').click();
    await page.getByRole('link', { name: 'Forum' }).click();
    await expect(page.locator('h1')).toContainText('Test Title Forum');
    await expect(page.locator('h1')).toContainText('Test Title Forum');
});





