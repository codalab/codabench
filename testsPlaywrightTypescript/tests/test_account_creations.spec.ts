import { test, expect } from '@playwright/test';
import { dbClient,testBadName,testmail,testPassword,testName } from '../config';

// Make the tests run in serial mode. We need them to be run in order otherwise they will fail.
test.describe.configure({ mode: 'serial' });

// This is run before each test
test.beforeAll(async ({}) => {
    console.log('Connecting to the Database');
    await dbClient.connect();
    console.log('Connected to the Database');
});
// This is run after each test
test.afterAll(async ({}) => {
    await dbClient.end();
    console.log('Closing Database Connection');
});


test('Test Failed account creation (illegal character in name)', async ({ browser }) => {
    // Create a new incognito browser context
    const context = await browser.newContext();
    context.clearCookies();
    // Create a new page inside context.
    const page = await context.newPage();
    await page.goto('');
    await page.getByRole('link', { name: 'Sign-up' }).click();
    await page.getByRole('textbox', { name: 'username' }).click();
    await page.getByRole('textbox', { name: 'username' }).fill(testBadName);
    await page.getByRole('textbox', { name: 'email' }).click();
    await page.getByRole('textbox', { name: 'email' }).fill(testmail);
    await page.getByRole('textbox', { name: 'password', exact: true }).click();
    await page.getByRole('textbox', { name: 'password', exact: true }).fill(testPassword);
    await page.getByRole('textbox', { name: 'confirm password' }).click();
    await page.getByRole('textbox', { name: 'confirm password' }).fill(testPassword);
    await page.getByRole('checkbox', { name: 'I accept the terms and' }).check();
    await page.getByRole('button', { name: 'Sign Up' }).click();
    await expect(page.getByText('Username can only contain lowercase letters, numbers, hyphens, and underscores.')).toBeVisible();
    await context.close();
});


test('Test Account creation from UI with Database query', async ({ browser }) => {
    // Create a new incognito browser context
    const context = await browser.newContext();
    context.clearCookies();
    // Create a new page inside context.
    const page = await context.newPage();
    await page.goto('');
    await page.getByRole('link', { name: 'Sign-up' }).click();
    await page.getByRole('textbox', { name: 'username' }).click();
    await page.getByRole('textbox', { name: 'username' }).fill(testName);
    await page.getByRole('textbox', { name: 'email' }).click();
    await page.getByRole('textbox', { name: 'email' }).fill(testmail);
    await page.getByRole('textbox', { name: 'password', exact: true }).click();
    await page.getByRole('textbox', { name: 'password', exact: true }).fill(testPassword);
    await page.getByRole('textbox', { name: 'confirm password' }).click();
    await page.getByRole('textbox', { name: 'confirm password' }).fill(testPassword);
    await page.getByRole('checkbox', { name: 'I accept the terms and' }).check();
    await page.getByRole('button', { name: 'Sign Up' }).click();

    const joinQuery = `SELECT username FROM profiles_user;`

    try {
        const queryResult = await dbClient.query(joinQuery);
        //expect(queryResult.rows.length).toBe(3);
        expect(queryResult.rows.find(e => e.username === testName).username).toContain(testName);
    } catch (err) {
        console.error(err.message);
        throw err;
    }
    await context.close();
});


test('Activate previously created account via database query', async () => {

    const selectQuery = `UPDATE profiles_user SET is_active = 't' WHERE username = '${testName}';`

    try {
        const selectResult = await dbClient.query(selectQuery);
        expect(selectResult.rowCount).toBe(1);
        expect(selectResult.command).toBe('UPDATE')

    } catch (err) {
        console.error(err.message);
        throw err;;
    }
});


test('Test Logging into the newly created and activated account', async ({ browser }) => {
    // Create a new incognito browser context
    const context = await browser.newContext();
    context.clearCookies();
    // Create a new page inside context.
    const page = await context.newPage();
    await page.goto('');
    await page.getByRole('link', { name: 'Login' }).click();
    await page.getByRole('textbox', { name: 'username or email' }).click();
    await page.getByRole('textbox', { name: 'username or email' }).fill(testName);
    await page.getByRole('textbox', { name: 'password' }).click();
    await page.getByRole('textbox', { name: 'password' }).fill(testPassword);
    await page.getByRole('button', { name: 'Log In' }).click();
    await expect(page.locator('#user_dropdown')).toContainText(testName);
    await context.close();
});