import { test, expect } from '@playwright/test';
import { username,password } from '../config';

test('Test Login', async ({ browser }) => {
    // Create a new incognito browser context
    const context = await browser.newContext();
    context.clearCookies();
    // Create a new page inside context.
    const page = await context.newPage();
    await page.goto('');
    await page.getByRole('link', { name: 'Login' }).click();
    await page.getByRole('textbox', { name: 'username or email' }).click();
    await page.getByRole('textbox', { name: 'username or email' }).fill(username);
    await page.getByRole('textbox', { name: 'password' }).click();
    await page.getByRole('textbox', { name: 'password' }).fill(password);
    await page.getByRole('button', { name: 'Log In' }).click();
    await expect(page.locator('#user_dropdown')).toContainText(username);
    context.close();
});