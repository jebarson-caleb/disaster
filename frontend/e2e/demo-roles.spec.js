import { expect, test } from '@playwright/test';

const demoE2eEnabled = globalThis.process?.env.DEMO_E2E === 'true';
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
    views: [
      ['Fire Rescue', 'Track rescue hazards, teams and equipment'],
      ['Rescue Queue', 'Rescue requests'],
      ['Field Report', 'Report a disaster'],
      ['Public Warnings', 'Alert dissemination'],
      ['Response Hub', responseHubHeading],
    ],
  },
];

test.describe('controlled full-stack role acceptance', () => {
  test.skip(!demoE2eEnabled, 'Runs only against the isolated demo acceptance environment.');

  test('every supported role can open each advertised workspace', async ({ page }) => {
    await page.goto('/');
    const rolePicker = page.getByLabel('Active role');
    await expect(rolePicker).toBeVisible();

    for (const workspace of roleWorkspaces) {
      await rolePicker.selectOption(workspace.role);
      await expect(rolePicker).toHaveValue(workspace.role);
      await expect(page.getByRole('heading', { name: workspace.topHeading, level: 1 })).toBeVisible();
      await expect(page.getByText(/connected to the live response API in demo mode/)).toBeVisible();

      for (const [navigationLabel, viewHeading] of workspace.views) {
        const navigationButton = page
          .getByRole('navigation', { name: 'Main views' })
          .getByRole('button', { name: navigationLabel, exact: true });
        await expect(navigationButton).toBeVisible();
        await navigationButton.click();
        await expect(page.getByRole('heading', { name: viewHeading, level: 2 })).toBeVisible();
      }

      if (workspace.dashboardAction) {
        const [actionLabel, actionHeading] = workspace.dashboardAction;
        await page
          .getByRole('navigation', { name: 'Main views' })
          .getByRole('button', { name: workspace.views[0][0], exact: true })
          .click();
        await page.getByRole('button', { name: actionLabel, exact: true }).click();
        await expect(page.getByRole('heading', { name: actionHeading, level: 2 })).toBeVisible();
      }
    }
  });

  test('an authorized operator can publish a warning and see delivery state', async ({ page }) => {
    const audience = `Browser acceptance zone ${Date.now()}`;
    await page.goto('/');
    await page.getByLabel('Active role').selectOption('Admin');
    await page
      .getByRole('navigation', { name: 'Main views' })
      .getByRole('button', { name: 'Public Warnings', exact: true })
      .click();

    await page.getByLabel('Audience').fill(audience);
    await page.getByLabel('Channel').fill('Operations dashboard');
    await page.getByLabel('Message').fill('This is an isolated acceptance warning.');
    await page.getByLabel('Action instruction').fill('No real-world action is required.');
    await page.getByRole('button', { name: 'Send alert', exact: true }).click();

    await expect(
      page.getByText(
        `Alert published in ResQ for ${audience}; no external delivery provider is configured.`,
      ),
    ).toBeVisible();
    const createdAlert = page.getByText(audience, { exact: true }).locator('..');
    await expect(createdAlert).toBeVisible();
    await expect(createdAlert.getByText('Delivery not configured', { exact: true })).toBeVisible();
  });
});
