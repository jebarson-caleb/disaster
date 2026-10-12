import { expect, test } from '@playwright/test';

const expectedDemoUrl = globalThis.process?.env.DEMO_BASE_URL || '';

async function expectDemoLink(page) {
  const demoLink = page.getByRole('link', { name: 'Play demo', exact: true });
  if (!expectedDemoUrl) {
    await expect(demoLink).toHaveCount(0);
    return;
  }

  await expect(demoLink).toBeVisible();
  await expect(demoLink).toHaveAttribute('href', new URL(expectedDemoUrl).href);
  await expect(demoLink).toHaveAttribute('target', '_blank');
  await expect(demoLink).toHaveAttribute('rel', 'noopener noreferrer');
}

test('public account modes isolate credentials and recovery tokens', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Sign in to your operational account' })).toBeVisible();
  await expectDemoLink(page);

  await page.getByLabel('Email').fill('mode-switch-test@example.invalid');
  const loginPassword = page.locator('input[name="password"]');
  await expect(loginPassword).not.toHaveAttribute('minlength');
  await loginPassword.fill('Browser-Smoke-Only-Password-91');
  await page.getByRole('button', { name: 'Show password', exact: true }).click();
  await expect(loginPassword).toHaveAttribute('type', 'text');
  await page.getByRole('button', { name: 'Hide password', exact: true }).click();
  await expect(loginPassword).toHaveAttribute('type', 'password');
  await page.getByRole('button', { name: 'Create an account' }).click();

  await expect(page.getByRole('heading', { name: 'Create a citizen or volunteer account' })).toBeVisible();
  await expect(page.getByLabel('Account role')).toHaveValue('Citizen');
  await expect(page.getByLabel('Email')).toHaveValue('');
  await expect(page.locator('input[name="new_password"]')).toHaveAttribute('minlength', '15');
  await expect(page.locator('input[name="new_password"]')).toHaveValue('');
  await expect(page.locator('input[name="password_confirmation"]')).toHaveValue('');

  await page.getByRole('button', { name: 'I already have an account' }).click();
  await page.getByRole('button', { name: 'Forgot password' }).click();
  await expect(page.getByRole('heading', { name: 'Request a password reset link' })).toBeVisible();
  await page.getByRole('button', { name: 'Back to sign in' }).click();
  await expect(page.getByRole('heading', { name: 'Sign in to your operational account' })).toBeVisible();
  await expectDemoLink(page);

  await page.goto('/?reset_token=invalid-browser-smoke-token');
  await expect(page.getByRole('heading', { name: 'Choose a new account password' })).toBeVisible();
  await page.getByRole('button', { name: 'Back to sign in' }).click();
  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByLabel('Email')).toHaveValue('');
  await expect(page.locator('input[name="password"]')).toHaveValue('');
});

test('public account access remains usable at a mobile viewport', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');

  await expect(page.getByRole('heading', { name: 'Sign in to your operational account' })).toBeVisible();
  await expect(page.getByLabel('Email')).toBeVisible();
  await expect(page.locator('input[name="password"]')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Sign in' })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});
