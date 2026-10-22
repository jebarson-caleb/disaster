import { expect, test } from '@playwright/test';

const responseHubHeading = 'Alerts, live field news, family tracing, rescue aid, and verified relief';

const roleWorkspaces = [
  {
    role: 'Admin',
    topHeading: 'Emergency coordination center',
    views: [
      ['Command', 'India-wide live risk and relief readiness'],
      ['Report Disaster', 'Report a disaster'],
      ['Rescue Queue', 'Rescue requests'],
      ['Public Warnings', 'Alert dissemination'],
      ['Facilities', 'Hospitals'],
      ['Relief Coordination', 'Move supplies and people to verified needs'],
      ['User Access', 'Provision an operational account'],
      ['Operational Setup', 'Add resource inventory'],
      ['Response Hub', responseHubHeading],
    ],
  },
  {
    role: 'Citizen',
    topHeading: 'Report, track and stay safe',
    department: 'Closed and restricted roads',
    views: [
      ['My Safety', 'Get help, follow warnings and reach safe shelter'],
      ['Report Help', 'Report a disaster'],
      ['Track Request', 'My rescue tracking'],
      ['Family & Aid', responseHubHeading],
    ],
  },
  {
    role: 'Hospital',
    topHeading: 'Capacity, triage and patient flow',
    department: 'Emergency surge readiness',
    views: [
      ['Hospital Ops', 'Manage surge capacity and incoming triage'],
      ['Capacity', 'My hospital capacity'],
      ['Incoming Triage', 'Incoming triage requests'],
      ['Response Hub', responseHubHeading],
    ],
  },
  {
    role: 'Shelter',
    topHeading: 'Occupancy, intake and relief supplies',
    department: 'Camp services check',
    views: [
      ['Shelter Ops', 'Track occupancy, intake and relief support'],
      ['Capacity', 'My shelter capacity'],
      ['Expected Arrivals', 'Rescue requests'],
      ['Response Hub', responseHubHeading],
    ],
    dashboardAction: ['View arrivals', 'Rescue requests'],
  },
  {
    role: 'Ambulance',
    topHeading: 'Assigned calls, ETA and hospital handoff',
    department: 'Vehicle readiness',
    views: [
      ['Dispatch', 'Prioritize calls, ETA and hospital handoff'],
      ['Assigned Calls', 'Rescue requests'],
      ['Hospitals', 'My ambulance status'],
      ['Response Hub', responseHubHeading],
    ],
  },
  {
    role: 'NGO',
    topHeading: 'Distribution, volunteers and unmet needs',
    department: 'Relief logistics check',
    views: [
      ['Relief Ops', 'Coordinate supplies, volunteers and unmet needs'],
      ['Needs Queue', 'Rescue requests'],
      ['Shelters', 'Shelters'],
      ['Field Report', 'Report a disaster'],
      ['Public Warnings', 'Alert dissemination'],
      ['Relief Coordination', 'Move supplies and people to verified needs'],
      ['Response Hub', responseHubHeading],
    ],
  },
  {
    role: 'Volunteer',
    topHeading: 'Assignments, safety and check-in',
    department: 'My availability and assignments',
    views: [
      ['My Assignment', 'Know your task, stay safe and check in'],
      ['Tasks', 'Volunteer tasks'],
      ['Report Hazard', 'Report a disaster'],
      ['Response Hub', responseHubHeading],
    ],
    dashboardAction: ['Report hazard', 'Report a disaster'],
  },
  {
    role: 'Police',
    topHeading: 'Perimeters, road access and crowd safety',
    department: 'Road closures and diversions',
    views: [
      ['Public Safety', 'Secure access, perimeters and rescue corridors'],
      ['Queue', 'Rescue requests'],
      ['Incident Report', 'Report a disaster'],
      ['Public Warnings', 'Alert dissemination'],
      ['Response Hub', responseHubHeading],
    ],
  },
  {
    role: 'Fire Service',
    topHeading: 'Rescue hazards, teams and equipment',
    department: 'Equipment and crew readiness',
    views: [
      ['Fire Rescue', 'Track rescue hazards, teams and equipment'],
      ['Rescue Queue', 'Rescue requests'],
      ['Field Report', 'Report a disaster'],
      ['Public Warnings', 'Alert dissemination'],
      ['Response Hub', responseHubHeading],
    ],
  },
];

function navigation(page, label) {
  return page.getByRole('navigation', { name: 'Main views' }).getByRole('button', { name: label, exact: true });
}

async function startDemo(page, role) {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Sign in to your operational account' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Try the interactive demo' })).toBeVisible();
  const apiRequests = [];
  page.on('request', (request) => {
    if (new URL(request.url()).pathname.startsWith('/api/')) apiRequests.push(`${request.method()} ${request.url()}`);
  });
  await page.getByRole('button', { name: `Demo as ${role}`, exact: true }).click();
  await expect(page.getByRole('note', { name: 'Demo environment notice' })).toContainText('never sent to live operations');
  return apiRequests;
}

test.describe('login-screen role demo', () => {
  test('every role demo opens each advertised workspace without contacting the API', async ({ page }) => {
    test.setTimeout(120_000);
    const apiRequests = await startDemo(page, 'Admin');
    const rolePicker = page.getByLabel('Active role');
    await expect(rolePicker).toBeEnabled();

    for (const workspace of roleWorkspaces) {
      await rolePicker.selectOption(workspace.role);
      await expect(rolePicker).toHaveValue(workspace.role);
      await expect(page.getByRole('heading', { name: workspace.topHeading, level: 1 })).toBeVisible();
      await expect(page.getByRole('button', { name: 'Demo data', exact: true })).toBeVisible();
      if (workspace.department) {
        await expect(page.getByRole('heading', { name: workspace.department, level: 2 })).toBeVisible();
      }

      for (const [navigationLabel, viewHeading] of workspace.views) {
        await navigation(page, navigationLabel).click();
        await expect(page.getByRole('heading', { name: viewHeading, level: 2 }).first()).toBeVisible();
        if (navigationLabel === 'Operational Setup') {
          await expect(page.getByRole('heading', { name: 'Integration readiness', level: 2 })).toBeVisible();
        }
      }

      if (workspace.dashboardAction) {
        const [actionLabel, actionHeading] = workspace.dashboardAction;
        await navigation(page, workspace.views[0][0]).click();
        await page.getByRole('button', { name: actionLabel, exact: true }).click();
        await expect(page.getByRole('heading', { name: actionHeading, level: 2 })).toBeVisible();
      }
    }

    expect(apiRequests).toEqual([]);
  });

  test('a demo operator can publish a warning and exit back to sign-in', async ({ page }) => {
    const apiRequests = await startDemo(page, 'Admin');
    const audience = `Demo acceptance zone ${Date.now()}`;
    await navigation(page, 'Public Warnings').click();
    await page.getByLabel('Audience').fill(audience);
    await page.getByLabel('Channel').fill('Operations dashboard');
    await page.getByLabel('Message').fill('This is a sandbox warning.');
    await page.getByLabel('Action instruction').fill('No real-world action is required.');
    await page.getByRole('button', { name: 'Send alert', exact: true }).click();
    await expect(page.getByText(`Alert published in ResQ for ${audience}; no external delivery provider is configured.`)).toBeVisible();

    await page.getByRole('button', { name: 'Exit demo', exact: true }).first().click();
    await expect(page.getByRole('heading', { name: 'Sign in to your operational account' })).toBeVisible();
    await expect(page.getByText(audience)).toHaveCount(0);
    expect(apiRequests).toEqual([]);
  });

  test('department tools record closures, readiness, and duty status', async ({ page }) => {
    await startDemo(page, 'Police');
    await page.getByRole('button', { name: 'Report a closure', exact: true }).click();
    await page.getByLabel('Road or junction').fill('Sandbox Bridge Road');
    await page.getByLabel('Location / landmark').fill('Sandbox junction');
    await page.getByLabel('Latitude').fill('12.98');
    await page.getByLabel('Longitude').fill('80.22');
    await page.getByLabel('Reason').fill('Bridge approach under water.');
    await page.getByRole('button', { name: 'Publish closure', exact: true }).click();
    await expect(page.getByText('Sandbox Bridge Road published as closed')).toBeVisible();

    await page.getByLabel('Active role').selectOption('Fire Service');
    await page.getByLabel('Hydraulic extrication tools').check();
    await page.getByRole('button', { name: 'Record readiness', exact: true }).click();
    await expect(page.getByText(/items ready/)).toBeVisible();

    await page.getByLabel('Active role').selectOption('Volunteer');
    await page.getByRole('button', { name: 'Mark complete', exact: true }).first().click();
    await expect(page.getByText('Assignment marked completed')).toBeVisible();
    await page.getByRole('button', { name: 'Off duty', exact: true }).click();
    await expect(page.getByText('Duty status changed to off duty')).toBeVisible();

    await page.getByLabel('Active role').selectOption('Citizen');
    await expect(page.getByText('Sandbox Bridge Road').first()).toBeVisible();
  });

  test('the demo launcher is usable at a mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await startDemo(page, 'Citizen');
    await expect(page.getByRole('heading', { name: 'Report, track and stay safe', level: 1 })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  });
});
