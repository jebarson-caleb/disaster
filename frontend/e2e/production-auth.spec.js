import { expect, test } from '@playwright/test';

test('public account modes isolate credentials and recovery tokens', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Sign in to your operational account' })).toBeVisible();

  await page.getByLabel('Email').fill('mode-switch-test@example.invalid');
  await expect(page.getByLabel('Password')).not.toHaveAttribute('minlength');
  await page.getByLabel('Password').fill('Browser-Smoke-Only-Password-91');
  await page.getByRole('button', { name: 'Create an account' }).click();

  await expect(page.getByRole('heading', { name: 'Create a citizen or volunteer account' })).toBeVisible();
  await expect(page.getByLabel('Account role')).toHaveValue('Citizen');
  await expect(page.getByLabel('Email')).toHaveValue('');
  await expect(page.getByLabel('Password (15+ characters)')).toHaveAttribute('minlength', '15');
  await expect(page.getByLabel('Password (15+ characters)')).toHaveValue('');
  await expect(page.getByLabel('Confirm password')).toHaveValue('');

  await page.getByRole('button', { name: 'I already have an account' }).click();
  await page.getByRole('button', { name: 'Forgot password' }).click();
  await expect(page.getByRole('heading', { name: 'Request a password reset link' })).toBeVisible();
  await page.getByRole('button', { name: 'Back to sign in' }).click();
  await expect(page.getByRole('heading', { name: 'Sign in to your operational account' })).toBeVisible();

  await page.goto('/?reset_token=invalid-browser-smoke-token');
  await expect(page.getByRole('heading', { name: 'Choose a new account password' })).toBeVisible();
  await page.getByRole('button', { name: 'Back to sign in' }).click();
  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByLabel('Email')).toHaveValue('');
  await expect(page.getByLabel('Password')).toHaveValue('');
});

test('public account access remains usable at a mobile viewport', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');

  await expect(page.getByRole('heading', { name: 'Sign in to your operational account' })).toBeVisible();
  await expect(page.getByLabel('Email')).toBeVisible();
  await expect(page.getByLabel('Password')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Sign in' })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});
