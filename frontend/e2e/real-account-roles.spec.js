import { expect, test } from '@playwright/test';

const realAccountE2eEnabled = globalThis.process?.env.REAL_ACCOUNT_E2E === 'true';
const expectedDemoUrl = globalThis.process?.env.DEMO_BASE_URL || 'https://demo.example.invalid/';
const accountPassword = 'DemoPassword123!';

const roleAccounts = [
  {
    role: 'Citizen',
    name: 'Kavya Raman',
    email: 'citizen@rescue.local',
    heading: 'Report, track and stay safe',
  },
  {
    role: 'Volunteer',
    name: 'Ravi Kumar',
    email: 'volunteer@rescue.local',
    heading: 'Assignments, safety and check-in',
  },
  {
    role: 'Police',
    name: 'Police Control Room',
    email: 'police@rescue.local',
    heading: 'Perimeters, road access and crowd safety',
  },
  {
    role: 'Fire Service',
    name: 'Fire Control Officer',
    email: 'fire@rescue.local',
    heading: 'Rescue hazards, teams and equipment',
  },
  {
    role: 'Hospital',
    name: 'Hospital Duty Officer',
    email: 'hospital@rescue.local',
    heading: 'Capacity, triage and patient flow',
  },
  {
    role: 'Shelter',
    name: 'Shelter Coordinator',
    email: 'shelter@rescue.local',
    heading: 'Occupancy, intake and relief supplies',
  },
  {
    role: 'Ambulance',
    name: '108 Dispatcher',
    email: 'ambulance@rescue.local',
    heading: 'Assigned calls, ETA and hospital handoff',
  },
  {
    role: 'NGO',
    name: 'Relief NGO Lead',
    email: 'ngo@rescue.local',
    heading: 'Distribution, volunteers and unmet needs',
  },
  {
    role: 'Admin',
    name: 'Incident Commander',
    email: 'admin@rescue.local',
    heading: 'Emergency coordination center',
  },
];

async function submitPassword(page, account) {
  await expect(page.getByRole('heading', { name: 'Sign in to your operational account' })).toBeVisible();
  await page.getByLabel('Email').fill(account.email);
  await page.locator('input[name="password"]').fill(accountPassword);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
}

async function expectWorkspace(page, account) {
  await expect(page.getByRole('heading', { name: account.heading, level: 1 })).toBeVisible();
  const rolePicker = page.getByLabel('Active role');
  await expect(rolePicker).toHaveValue(account.role);
  await expect(rolePicker).toBeDisabled();
  await expect(page.getByRole('button', { name: 'Live API', exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Log out', exact: true })).toBeVisible();
}

async function signOut(page) {
  const signOutButton = page.getByRole('button', { name: 'Log out', exact: true });
  const [response] = await Promise.all([
    page.waitForResponse((item) => (
      item.url().endsWith('/api/v1/auth/logout') && item.request().method() === 'POST'
    )),
    signOutButton.click(),
  ]);
  expect(response.status()).toBe(200);
  await expect(page.getByRole('heading', { name: 'Sign in to your operational account' })).toBeVisible();
}

test.describe('production-mode account acceptance', () => {
  test.skip(!realAccountE2eEnabled, 'Runs only against the isolated real-account acceptance environment.');
  test.describe.configure({ retries: 0 });

  test('every supported role signs in directly to its role-locked workspace', async ({ page }) => {
    test.setTimeout(180_000);
    page.on('pageerror', (error) => console.error(`Browser runtime error: ${error.message}`));
    page.on('requestfailed', (request) => console.error(
      `Request failed: ${request.method()} ${new URL(request.url()).pathname} ${request.failure()?.errorText}`,
    ));

    await page.goto('/');
    const demoLink = page.getByRole('link', { name: 'Play demo', exact: true });
    await expect(demoLink).toBeVisible();
    await expect(demoLink).toHaveAttribute('href', new URL(expectedDemoUrl).href);
    await expect(demoLink).toHaveAttribute('target', '_blank');
    await expect(demoLink).toHaveAttribute('rel', 'noopener noreferrer');

    for (const account of roleAccounts) {
      await page.goto('/');
      await submitPassword(page, account);

      await expectWorkspace(page, account);
      await signOut(page);
    }
  });
});
