import { Buffer } from 'node:buffer';
import { createHmac } from 'node:crypto';

import { expect, test } from '@playwright/test';

const realAccountE2eEnabled = globalThis.process?.env.REAL_ACCOUNT_E2E === 'true';
const accountPassword = 'DemoPassword123!';
const base32Alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
const privilegedRoles = new Set(['Admin', 'Police', 'Fire Service', 'Hospital', 'Shelter', 'Ambulance', 'NGO']);

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

function decodeBase32(value) {
  let bits = '';
  for (const character of value.replace(/=+$/u, '').toUpperCase()) {
    const index = base32Alphabet.indexOf(character);
    if (index < 0) throw new Error('Invalid base32 authenticator secret');
    bits += index.toString(2).padStart(5, '0');
  }
  const bytes = [];
  for (let offset = 0; offset + 8 <= bits.length; offset += 8) {
    bytes.push(Number.parseInt(bits.slice(offset, offset + 8), 2));
  }
  return Buffer.from(bytes);
}

function currentTotp(secret) {
  const counter = Math.floor(Date.now() / 1000 / 30);
  const counterBytes = Buffer.alloc(8);
  counterBytes.writeBigUInt64BE(BigInt(counter));
  const digest = createHmac('sha1', decodeBase32(secret)).update(counterBytes).digest();
  const offset = digest[digest.length - 1] & 0x0f;
  const value = (digest.readUInt32BE(offset) & 0x7fffffff) % 1_000_000;
  return String(value).padStart(6, '0');
}

async function submitPassword(page, account) {
  await expect(page.getByRole('heading', { name: 'Sign in to your operational account' })).toBeVisible();
  await page.getByLabel('Email').fill(account.email);
  await page.getByLabel('Password (15+ characters)').fill(accountPassword);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
}

async function expectWorkspace(page, account) {
  await expect(page.getByRole('heading', { name: account.heading, level: 1 })).toBeVisible();
  const rolePicker = page.getByLabel('Active role');
  await expect(rolePicker).toHaveValue(account.role);
  await expect(rolePicker).toBeDisabled();
  await expect(page.getByRole('button', { name: 'Live API', exact: true })).toBeVisible();
}

async function signOut(page, account) {
  const signOutButton = page.getByRole('button', { name: 'Sign out', exact: true });
  if (!(await signOutButton.isVisible())) {
    await page.getByRole('button', { name: account.name, exact: true }).click();
  }
  await signOutButton.click();
  await expect(page.getByRole('heading', { name: 'Sign in to your operational account' })).toBeVisible();
}

test.describe('production-mode account acceptance', () => {
  test.skip(!realAccountE2eEnabled, 'Runs only against the isolated real-account acceptance environment.');
  test.describe.configure({ retries: 0 });

  test('every supported role signs in through the real account and MFA UI', async ({ page }) => {
    test.setTimeout(180_000);

    for (const account of roleAccounts) {
      await page.goto('/');
      await submitPassword(page, account);

      if (privilegedRoles.has(account.role)) {
        await expect(page.getByText('Multi-factor authentication is required', { exact: true })).toBeVisible();
        await page.getByLabel('Current password').fill(accountPassword);
        await page.getByRole('button', { name: 'Start authenticator setup', exact: true }).click();

        const secret = (await page.locator('.mfa-secret code').innerText()).trim();
        await page.getByLabel('Six-digit code').fill(currentTotp(secret));
        await page.getByRole('button', { name: 'Confirm and enable MFA', exact: true }).click();

        await expectWorkspace(page, account);
        const recoveryCodes = await page.locator('.recovery-code-grid code').allTextContents();
        expect(recoveryCodes.length).toBeGreaterThan(0);
        const recoveryCode = recoveryCodes[0].trim();
        await signOut(page, account);

        await submitPassword(page, account);
        await expect(page.getByLabel('Verification code')).toBeVisible();
        await page.getByLabel('Verification code').fill(recoveryCode);
        await page.getByRole('button', { name: 'Verify and sign in', exact: true }).click();
      }

      await expectWorkspace(page, account);
      await signOut(page, account);
    }
  });
});
