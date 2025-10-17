import { test as setup, expect } from '@playwright/test';
import path from 'path';
import { username,password } from '../config';

const authFile = path.join(__dirname, '../playwright/.auth/user.json');

setup('Authenticate', async ({ page }) => {
  // Perform authentication steps. Replace these actions with your own.
  await page.goto('');
    await page.getByRole('link', { name: 'Login' }).click();
    await page.getByRole('textbox', { name: 'username or email' }).click();
    await page.getByRole('textbox', { name: 'username or email' }).fill(username);
    await page.getByRole('textbox', { name: 'password' }).click();
    await page.getByRole('textbox', { name: 'password' }).fill(password);
    await page.getByRole('button', { name: 'Log In' }).click();
  // Alternatively, you can wait until the page reaches a state where all cookies are set.
  await expect(page.locator('#user_dropdown')).toContainText(username);

  // End of authentication steps.

  await page.context().storageState({ path: authFile });
});