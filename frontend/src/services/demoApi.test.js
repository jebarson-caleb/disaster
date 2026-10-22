import assert from 'node:assert/strict';
import { test } from 'node:test';
import { createDemoClient } from './demoApi.js';

const fixedNow = () => Date.parse('2026-10-22T12:00:00Z');

test('the sandbox never performs network requests', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = () => {
    throw new Error('network access attempted');
  };
  try {
    const client = createDemoClient('Admin', { now: fixedNow });
    await client.bootstrap();
    await client.coordination();
    await client.createAlert({ audience: 'Test ward', channels: 'SMS', message: 'Test', instruction: 'None' });
    await client.adminUsers();
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('every role receives a scoped workspace snapshot', async () => {
  const roles = ['Admin', 'Citizen', 'Hospital', 'Shelter', 'Ambulance', 'NGO', 'Volunteer', 'Police', 'Fire Service'];
  const client = createDemoClient('Admin', { now: fixedNow });
  for (const role of roles) {
    client.setRole(role);
    const snapshot = await client.bootstrap();
    assert.ok(snapshot.disasters.length > 0, `${role} sees incidents`);
    assert.equal(client.currentUser().role, role);
  }

  client.setRole('Citizen');
  const citizen = await client.bootstrap();
  assert.ok(citizen.rescue_requests.every((item) => item.requester_id === 2));
  assert.deepEqual(citizen.resources, []);
  assert.deepEqual(citizen.response_hub.hospital_notifications, []);

  client.setRole('Hospital');
  const hospital = await client.bootstrap();
  assert.deepEqual(hospital.facilities.hospitals.map((item) => item.id), [1]);
  assert.deepEqual(hospital.facilities.shelters, []);

  client.setRole('Shelter');
  const shelter = await client.bootstrap();
  assert.ok(shelter.rescue_requests.length > 0);
  assert.ok(shelter.rescue_requests.every((item) => item.condition === 'stable'));

  client.setRole('Volunteer');
  const volunteer = await client.bootstrap();
  assert.equal(volunteer.field.volunteer.name, 'Ravi Kumar');
  assert.deepEqual(volunteer.rescue_requests.map((item) => item.id), [103]);
});

test('role permissions mirror the live API', async () => {
  const client = createDemoClient('Citizen', { now: fixedNow });
  await assert.rejects(client.createAlert({ audience: 'a', channels: 'b', message: 'c', instruction: 'd' }), { status: 403 });
  await assert.rejects(client.createRoadClosure({}), { status: 403 });

  client.setRole('Volunteer');
  await assert.rejects(client.updateRescue(103, { status: 'cancelled' }), { status: 403 });
  const updated = await client.updateRescue(103, { status: 'rescued' });
  assert.equal(updated.rescue_request.status, 'rescued');

  client.setRole('Hospital');
  await assert.rejects(client.updateHospital(2, { available_beds: 1 }), { status: 403 });
  await assert.rejects(client.updateHospital(1, { available_beds: 9999 }), { status: 400 });
});

test('a citizen rescue request is auto-dispatched and visible to command', async () => {
  const client = createDemoClient('Citizen', { now: fixedNow });
  const created = await client.createRescue({
    disaster_id: 1,
    victim_name: 'Sample person',
    condition: 'injured',
    people_count: 2,
    latitude: 12.98,
    longitude: 80.22,
  });
  assert.equal(created.rescue_request.status, 'assigned');
  assert.ok(created.automatic_allocation.hospital);

  client.setRole('Admin');
  const command = await client.bootstrap();
  assert.ok(command.rescue_requests.some((item) => item.id === created.rescue_request.id));
});

test('department field records round-trip through the sandbox', async () => {
  const client = createDemoClient('Police', { now: fixedNow });
  const { road_closure: closure } = await client.createRoadClosure({
    road_name: 'Sample road',
    location: 'Sample junction',
    latitude: 12.9,
    longitude: 80.2,
    reason: 'Flooded',
  });
  await client.updateRoadClosure(closure.id, { status: 'reopened' });
  const check = await client.createReadinessCheck({ subject: 'Shift A', items: { Radios: true, Barricades: false } });
  assert.equal(check.readiness_check.ready_count, 1);

  client.setRole('Citizen');
  const citizen = await client.bootstrap();
  assert.equal(citizen.field.road_closures.find((item) => item.id === closure.id).status, 'reopened');
  assert.deepEqual(citizen.field.readiness_checks, []);

  client.setRole('Volunteer');
  const assignment = (await client.bootstrap()).field.volunteer.assignments[0];
  const completed = await client.updateVolunteerAssignment(assignment.id, { status: 'completed' });
  assert.equal(completed.volunteer.availability_status, 'available');
  const offDuty = await client.updateVolunteerAvailability({ availability_status: 'off duty' });
  assert.equal(offDuty.volunteer.availability_status, 'off duty');
});

test('each sandbox starts from a fresh copy of the sample data', async () => {
  const first = createDemoClient('Admin', { now: fixedNow });
  await first.createDisaster({ title: 'Only in first', disaster_type: 'flood', address: 'x', description: 'y', latitude: 1, longitude: 1 });
  const second = createDemoClient('Admin', { now: fixedNow });
  const titles = (await second.bootstrap()).disasters.map((item) => item.title);
  assert.ok(!titles.includes('Only in first'));
});
