// In-browser implementation of the operational API used by the demo sandbox.
// It mirrors the live API's response shapes and server-side role scoping, but
// every read and write stays in memory in this tab: nothing reaches the server.

import { estimateDamage, prioritizeRescue } from './ai.js';
import { DEMO_USERS, createDemoState } from './demoData.js';
import { distanceKm, nearestItem } from './geo.js';

const COMMAND_ROLES = new Set(['Admin', 'Police', 'Fire Service', 'NGO']);
const WELFARE_ROLES = new Set(['Admin', 'Police', 'Fire Service', 'NGO', 'Volunteer']);
const SUPPLY_ROLES = new Set(['Admin', 'NGO', 'Shelter', 'Police', 'Fire Service']);
const RESOURCE_ROLES = new Set(['Admin', 'NGO', 'Shelter']);
const READINESS_ROLES = new Set(['Admin', 'Police', 'Fire Service', 'Hospital', 'Shelter', 'Ambulance', 'NGO', 'Volunteer']);
const RESPONDER_VIEW_ROLES = new Set(['Admin', 'Police', 'Fire Service', 'NGO', 'Shelter', 'Ambulance', 'Volunteer']);
const LIMITED_ROLE_STATUSES = {
  Hospital: new Set(['triage', 'rescued']),
  Ambulance: new Set(['en route', 'triage', 'rescued']),
  Volunteer: new Set(['en route', 'rescued']),
};
const SHELTER_ARRIVAL_RADIUS_KM = 30;

function rejection(message, status = 400) {
  const error = new Error(message);
  error.status = status;
  return error;
}

function copy(value) {
  return structuredClone(value);
}

export function createDemoClient(initialRole = 'Citizen', { now = () => Date.now() } = {}) {
  const state = createDemoState(now());
  let role = initialRole;

  const timestamp = () => new Date(now()).toISOString();
  const nextId = () => {
    state.nextId += 1;
    return state.nextId;
  };
  const user = () => DEMO_USERS[role];
  const facilityId = (type) => (user().managed_facility?.type === type ? user().managed_facility.id : null);
  const ownVolunteer = () => state.volunteers.find((item) => item.user_id === user().id) || null;

  function require(roles) {
    if (!roles.has(role)) throw rejection('Forbidden for this role', 403);
  }

  function find(collection, id, label) {
    const item = collection.find((entry) => Number(entry.id) === Number(id));
    if (!item) throw rejection(`${label} not found`, 404);
    return item;
  }

  function requiredText(payload, field, maxLength) {
    const value = String(payload[field] ?? '').trim();
    if (!value) throw rejection(`${field} is required`);
    if (value.length > maxLength) throw rejection(`${field} must contain at most ${maxLength} characters`);
    return value;
  }

  function coordinate(value, field, limit) {
    const number = Number(value);
    if (value === '' || value == null || !Number.isFinite(number) || Math.abs(number) > limit) {
      throw rejection(`${field} is outside valid bounds`);
    }
    return number;
  }

  function assignedRescueIds() {
    if (role === 'Hospital') {
      return state.hospitalNotifications.filter((item) => item.hospital_id === facilityId('hospital')).map((item) => item.rescue_request_id);
    }
    if (role === 'Ambulance') {
      return state.dispatches.filter((item) => item.responder_type === 'ambulance' && item.responder_id === facilityId('ambulance')).map((item) => item.rescue_request_id);
    }
    if (role === 'Volunteer') {
      const volunteer = ownVolunteer();
      return state.dispatches.filter((item) => item.responder_type === 'volunteer' && item.responder_id === volunteer?.id).map((item) => item.rescue_request_id);
    }
    if (role === 'Shelter') {
      const shelter = state.shelters.find((item) => item.id === facilityId('shelter'));
      if (!shelter) return [];
      return state.rescues
        .filter((item) => item.condition === 'stable' && ['assigned', 'en route'].includes(item.status))
        .filter((item) => (distanceKm(item, shelter) ?? Infinity) <= SHELTER_ARRIVAL_RADIUS_KM)
        .map((item) => item.id);
    }
    return [];
  }

  function visibleRescues() {
    const ordered = [...state.rescues].sort((a, b) => b.priority_score - a.priority_score);
    if (COMMAND_ROLES.has(role)) return ordered;
    if (role === 'Citizen') return ordered.filter((item) => item.requester_id === user().id);
    const ids = new Set(assignedRescueIds());
    return ordered.filter((item) => ids.has(item.id));
  }

  function visibleFacilities() {
    if (role === 'Hospital') {
      return { hospitals: state.hospitals.filter((item) => item.id === facilityId('hospital')), shelters: [], ambulances: [] };
    }
    if (role === 'Shelter') {
      return { hospitals: [], shelters: state.shelters.filter((item) => item.id === facilityId('shelter')), ambulances: [] };
    }
    if (role === 'Ambulance') {
      return { hospitals: state.hospitals, shelters: [], ambulances: state.ambulances.filter((item) => item.id === facilityId('ambulance')) };
    }
    return { hospitals: state.hospitals, shelters: state.shelters, ambulances: state.ambulances };
  }

  function visibleHospitalNotifications() {
    if (role === 'Admin') return state.hospitalNotifications;
    if (role === 'Hospital') return state.hospitalNotifications.filter((item) => item.hospital_id === facilityId('hospital'));
    if (role === 'Ambulance') {
      const ids = new Set(assignedRescueIds());
      return state.hospitalNotifications.filter((item) => ids.has(item.rescue_request_id));
    }
    return [];
  }

  function visibleDispatches() {
    if (['Admin', 'Police', 'Fire Service', 'NGO'].includes(role)) return state.dispatches;
    if (role === 'Ambulance') return state.dispatches.filter((item) => item.responder_type === 'ambulance' && item.responder_id === facilityId('ambulance'));
    if (role === 'Volunteer') return state.dispatches.filter((item) => item.responder_type === 'volunteer' && item.responder_id === ownVolunteer()?.id);
    return [];
  }

  function volunteerPayload() {
    const volunteer = ownVolunteer();
    if (!volunteer) return null;
    return { ...volunteer, assignments: state.volunteerAssignments.filter((item) => item.volunteer_id === volunteer.id) };
  }

  function alertPayload(alert) {
    const acknowledged = state.acknowledgedAlertIds.includes(`${role}:${alert.id}`);
    const base = { ...alert, acknowledged };
    if (!COMMAND_ROLES.has(role)) {
      delete base.delivery_status;
      delete base.delivery_attempts;
    }
    return base;
  }

  function releaseResponders(rescueId, finalStatus) {
    for (const dispatch of state.dispatches.filter((item) => item.rescue_request_id === rescueId)) {
      dispatch.status = finalStatus;
      if (dispatch.responder_type === 'rescue_unit') {
        const unit = state.responderUnits.find((item) => item.id === dispatch.responder_id);
        if (unit) unit.availability_status = 'available';
      } else if (dispatch.responder_type === 'volunteer') {
        const volunteer = state.volunteers.find((item) => item.id === dispatch.responder_id);
        if (volunteer) volunteer.availability_status = 'available';
      } else if (dispatch.responder_type === 'ambulance') {
        const ambulance = state.ambulances.find((item) => item.id === dispatch.responder_id);
        if (ambulance) ambulance.status = 'available';
      }
    }
  }

  function autoDispatch(rescue, disaster) {
    const allocation = { rescue_unit: null, volunteer: null, ambulance: null, hospital: null };
    const names = [];
    const addDispatch = (type, responder, name, distance) => {
      state.dispatches.unshift({ id: nextId(), rescue_request_id: rescue.id, responder_type: type, responder_id: responder.id, responder_name: name, distance_km: Number(distance.toFixed(1)), status: 'assigned', created_at: timestamp() });
      names.push(name);
    };
    const unit = nearestItem(rescue, state.responderUnits.filter((item) => item.availability_status === 'available'));
    if (unit) {
      unit.item.availability_status = 'dispatched';
      addDispatch('rescue_unit', unit.item, unit.item.name, unit.distance);
      allocation.rescue_unit = { name: unit.item.name, distance_km: unit.distance };
    }
    const volunteer = nearestItem(rescue, state.volunteers.filter((item) => item.availability_status === 'available'));
    if (volunteer) {
      volunteer.item.availability_status = 'assigned';
      state.volunteerAssignments.unshift({ id: nextId(), volunteer_id: volunteer.item.id, disaster_id: disaster.id, task: `Automatic nearby dispatch for rescue #${rescue.id}: assist ${rescue.victim_name}`, status: 'assigned', assigned_at: timestamp() });
      addDispatch('volunteer', volunteer.item, volunteer.item.name, volunteer.distance);
      allocation.volunteer = { name: volunteer.item.name, distance_km: volunteer.distance };
    }
    const needsAmbulance = rescue.priority_score >= 60 || ['injured', 'critical', 'unconscious', 'bleeding'].includes(rescue.condition);
    const ambulance = needsAmbulance ? nearestItem(rescue, state.ambulances.filter((item) => item.status === 'available')) : null;
    if (ambulance) {
      ambulance.item.status = 'dispatched';
      addDispatch('ambulance', ambulance.item, ambulance.item.vehicle_number, ambulance.distance);
      allocation.ambulance = { vehicle_number: ambulance.item.vehicle_number, distance_km: ambulance.distance };
    }
    const hospital = nearestItem(rescue, state.hospitals.filter((item) => item.available_beds > 0));
    if (hospital) {
      state.hospitalNotifications.unshift({ id: nextId(), hospital_id: hospital.item.id, disaster_id: disaster.id, rescue_request_id: rescue.id, expected_patients: rescue.people_count, priority: rescue.priority_label, message: `Prepare for ${rescue.people_count} incoming patient(s) from ${disaster.title}. Condition: ${rescue.condition}.`, status: 'sent', created_at: timestamp() });
      allocation.hospital = { name: hospital.item.name, distance_km: hospital.distance };
    }
    if (names.length) {
      rescue.assigned_unit = names.join(' + ');
      rescue.status = 'assigned';
    }
    return allocation;
  }

  const client = {
    isDemo: true,
    role: () => role,
    setRole(nextRole) {
      if (!DEMO_USERS[nextRole]) throw rejection('Unknown demo role');
      role = nextRole;
    },
    currentUser: () => copy({ ...user(), is_active: true, verification_status: 'verified', password_change_required: false }),

    async bootstrap() {
      return copy({
        disasters: [...state.disasters].sort((a, b) => b.created_at.localeCompare(a.created_at)),
        rescue_requests: visibleRescues(),
        facilities: visibleFacilities(),
        resources: RESOURCE_ROLES.has(role) ? state.resources : [],
        alerts: state.alerts.map(alertPayload),
        response_hub: {
          emergency_hotline: '112',
          news_updates: state.newsUpdates,
          welfare_checks: WELFARE_ROLES.has(role) ? state.welfareChecks : state.welfareChecks.filter((item) => item.requester_id === user().id),
          hospital_notifications: visibleHospitalNotifications(),
          supply_requests: SUPPLY_ROLES.has(role) ? state.supplyRequests : state.supplyRequests.filter((item) => item.requester_id === user().id),
          campaigns: state.campaigns,
          dispatches: visibleDispatches(),
          responder_units: RESPONDER_VIEW_ROLES.has(role) ? state.responderUnits : [],
        },
        field: {
          road_closures: [...state.roadClosures].sort((a, b) => Number(a.status === 'reopened') - Number(b.status === 'reopened')),
          readiness_checks: READINESS_ROLES.has(role) ? state.readinessChecks.filter((item) => role === 'Admin' || item.role === role) : [],
          volunteer: role === 'Volunteer' ? volunteerPayload() : null,
        },
        server_time: timestamp(),
      });
    },

    async coordination() {
      require(new Set(['Admin', 'NGO', 'Police', 'Fire Service']));
      return copy({ resources: state.resources, distributions: state.distributions, volunteers: state.volunteers, assignments: state.volunteerAssignments });
    },

    async createDisaster(payload) {
      const assessment = estimateDamage(payload);
      const disaster = {
        id: nextId(),
        title: requiredText(payload, 'title', 160),
        disaster_type: payload.disaster_type,
        address: requiredText(payload, 'address', 255),
        description: requiredText(payload, 'description', 4000),
        latitude: coordinate(payload.latitude, 'latitude', 90),
        longitude: coordinate(payload.longitude, 'longitude', 180),
        people_affected: Math.max(0, Number(payload.people_affected) || 0),
        severity_hint: payload.severity_hint,
        status: 'active',
        score: assessment.score,
        label: assessment.label,
        created_at: timestamp(),
      };
      state.disasters.unshift(disaster);
      return copy({ disaster, damage_estimation: assessment });
    },

    async updateDisasterStatus(id, { status }) {
      require(new Set(['Admin', 'Police', 'Fire Service']));
      const disaster = find(state.disasters, id, 'Incident');
      disaster.status = status;
      return copy({ disaster });
    },

    async createRescue(payload) {
      const disaster = find(state.disasters, payload.disaster_id, 'Incident');
      const priority = prioritizeRescue(payload, disaster.disaster_type);
      const rescue = {
        id: nextId(),
        disaster_id: disaster.id,
        requester_id: user().id,
        victim_name: requiredText(payload, 'victim_name', 120),
        victim_age: Number(payload.victim_age) || 0,
        people_count: Math.max(1, Number(payload.people_count) || 1),
        condition: payload.condition || 'stable',
        trapped: payload.trapped === true,
        vulnerable_people: Math.max(0, Number(payload.vulnerable_people) || 0),
        notes: String(payload.notes || ''),
        latitude: coordinate(payload.latitude, 'latitude', 90),
        longitude: coordinate(payload.longitude, 'longitude', 180),
        priority_score: priority.score,
        priority_label: priority.label,
        status: 'pending',
        assigned_unit: '',
        created_at: timestamp(),
        updated_at: timestamp(),
      };
      state.rescues.unshift(rescue);
      const automaticAllocation = autoDispatch(rescue, disaster);
      return copy({ rescue_request: rescue, priority, automatic_allocation: automaticAllocation });
    },

    async assignRescue(id, { assigned_unit: assignedUnit }) {
      require(COMMAND_ROLES);
      const rescue = find(state.rescues, id, 'Rescue request');
      if (state.dispatches.some((item) => item.rescue_request_id === rescue.id && item.status === 'assigned')) {
        throw rejection('This rescue already has an active dispatch', 409);
      }
      const unit = state.responderUnits.find((item) => item.name === assignedUnit);
      const ambulance = state.ambulances.find((item) => item.vehicle_number === assignedUnit);
      const asset = unit || ambulance;
      if (!asset) throw rejection('assigned_unit must match a registered responder unit or ambulance', 409);
      if ((unit && unit.availability_status !== 'available') || (ambulance && ambulance.status !== 'available')) {
        throw rejection('The selected unit is not available', 409);
      }
      if (unit) unit.availability_status = 'dispatched';
      if (ambulance) ambulance.status = 'dispatched';
      state.dispatches.unshift({ id: nextId(), rescue_request_id: rescue.id, responder_type: unit ? 'rescue_unit' : 'ambulance', responder_id: asset.id, responder_name: assignedUnit, distance_km: Number((distanceKm(rescue, asset) ?? 0).toFixed(1)), status: 'assigned', created_at: timestamp() });
      Object.assign(rescue, { assigned_unit: assignedUnit, status: 'assigned', updated_at: timestamp() });
      return copy({ rescue_request: rescue });
    },

    async updateRescue(id, { status, assigned_unit: assignedUnit }) {
      const rescue = find(state.rescues, id, 'Rescue request');
      if (!COMMAND_ROLES.has(role) && !assignedRescueIds().includes(rescue.id)) {
        throw rejection('This rescue request is not assigned to your account', 403);
      }
      const limited = LIMITED_ROLE_STATUSES[role];
      if (limited && !limited.has(status)) throw rejection(`Your role may set only: ${[...limited].join(', ')}`, 403);
      rescue.status = status;
      if (assignedUnit) rescue.assigned_unit = assignedUnit;
      rescue.updated_at = timestamp();
      if (['rescued', 'cancelled'].includes(status)) releaseResponders(rescue.id, status === 'rescued' ? 'completed' : 'cancelled');
      return copy({ rescue_request: rescue });
    },

    async updateHospital(id, payload) {
      require(new Set(['Admin', 'Hospital']));
      const hospital = find(state.hospitals, id, 'Hospital');
      if (role === 'Hospital' && hospital.id !== facilityId('hospital')) throw rejection('You can update only your assigned hospital', 403);
      const next = { ...hospital };
      for (const field of ['available_beds', 'icu_beds', 'emergency_capacity']) {
        if (payload[field] !== undefined) next[field] = Number(payload[field]);
      }
      if (!Number.isInteger(next.available_beds) || next.available_beds < 0 || next.available_beds > next.total_beds || next.icu_beds < 0 || next.emergency_capacity < 0) {
        throw rejection('Hospital capacity values are outside valid bounds');
      }
      Object.assign(hospital, next, { updated_at: timestamp() });
      return copy({ hospital });
    },

    async updateShelter(id, payload) {
      require(new Set(['Admin', 'Shelter']));
      const shelter = find(state.shelters, id, 'Shelter');
      if (role === 'Shelter' && shelter.id !== facilityId('shelter')) throw rejection('You can update only your assigned shelter', 403);
      const capacity = payload.available_capacity !== undefined ? Number(payload.available_capacity) : shelter.available_capacity;
      if (!Number.isInteger(capacity) || capacity < 0 || capacity > shelter.total_capacity) throw rejection('Shelter capacity is outside valid bounds');
      shelter.available_capacity = capacity;
      for (const field of ['food_available', 'medical_support']) {
        if (typeof payload[field] === 'boolean') shelter[field] = payload[field];
      }
      shelter.updated_at = timestamp();
      return copy({ shelter });
    },

    async updateAmbulance(id, payload) {
      require(new Set(['Admin', 'Ambulance']));
      const ambulance = find(state.ambulances, id, 'Ambulance');
      if (role === 'Ambulance' && ambulance.id !== facilityId('ambulance')) throw rejection('You can update only your assigned ambulance', 403);
      if (payload.status !== undefined) {
        if (!['available', 'dispatched', 'maintenance', 'offline'].includes(payload.status)) throw rejection('Invalid ambulance status');
        ambulance.status = payload.status;
      }
      if (payload.latitude !== undefined) {
        ambulance.latitude = coordinate(payload.latitude, 'latitude', 90);
        ambulance.longitude = coordinate(payload.longitude, 'longitude', 180);
      }
      ambulance.updated_at = timestamp();
      return copy({ ambulance });
    },

    async createAlert(payload) {
      require(COMMAND_ROLES);
      const alert = {
        id: nextId(),
        identifier: `RESQ-DEMO-${nextId()}`,
        event: payload.event || 'Multi-hazard public warning',
        audience: requiredText(payload, 'audience', 180),
        channels: requiredText(payload, 'channels', 180),
        message: requiredText(payload, 'message', 2000),
        instruction: requiredText(payload, 'instruction', 2000),
        urgency: 'immediate',
        severity: 'severe',
        certainty: 'likely',
        status: 'active',
        delivery_status: 'not_configured',
        delivery_attempts: 0,
        acknowledgement_count: 0,
        created_at: timestamp(),
      };
      state.alerts.unshift(alert);
      return copy({ alert, delivery: { status: 'not_configured', provider: 'none' } });
    },

    async retryAlertDelivery(id) {
      require(COMMAND_ROLES);
      const alert = find(state.alerts, id, 'Alert');
      alert.delivery_status = 'not_configured';
      return copy({ alert, delivery: { status: 'not_configured', provider: 'none' } });
    },

    async acknowledgeAlert(id) {
      const alert = find(state.alerts, id, 'Alert');
      const key = `${role}:${alert.id}`;
      const created = !state.acknowledgedAlertIds.includes(key);
      if (created) {
        state.acknowledgedAlertIds.push(key);
        alert.acknowledgement_count += 1;
      }
      return { acknowledgement: { alert_id: alert.id, response: 'received' }, created };
    },

    async createDistribution(payload) {
      require(new Set(['Admin', 'NGO', 'Shelter']));
      const resource = find(state.resources, payload.resource_id, 'Resource');
      find(state.disasters, payload.disaster_id, 'Incident');
      const quantity = Number(payload.quantity);
      if (!Number.isInteger(quantity) || quantity < 1 || quantity > resource.available_quantity) throw rejection('Requested quantity exceeds available inventory');
      resource.available_quantity -= quantity;
      const distribution = { id: nextId(), resource_id: resource.id, disaster_id: Number(payload.disaster_id), quantity, destination: requiredText(payload, 'destination', 180), status: 'planned', created_at: timestamp() };
      state.distributions.unshift(distribution);
      return copy({ distribution });
    },

    async createVolunteerAssignment(payload) {
      require(new Set(['Admin', 'NGO']));
      const volunteer = find(state.volunteers, payload.volunteer_id, 'Volunteer');
      find(state.disasters, payload.disaster_id, 'Incident');
      if (volunteer.availability_status !== 'available') throw rejection('Volunteer is not currently available', 409);
      volunteer.availability_status = 'assigned';
      const assignment = { id: nextId(), volunteer_id: volunteer.id, disaster_id: Number(payload.disaster_id), task: requiredText(payload, 'task', 180), status: 'assigned', assigned_at: timestamp() };
      state.volunteerAssignments.unshift(assignment);
      return copy({ assignment, volunteer });
    },

    async updateVolunteerAssignment(id, { status }) {
      require(new Set(['Admin', 'NGO', 'Volunteer']));
      const assignment = find(state.volunteerAssignments, id, 'Assignment');
      const volunteer = state.volunteers.find((item) => item.id === assignment.volunteer_id);
      if (role === 'Volunteer' && volunteer?.user_id !== user().id) throw rejection('You can update only your own assignments', 403);
      assignment.status = status;
      if (volunteer && ['completed', 'cancelled'].includes(status)) {
        const open = state.volunteerAssignments.some((item) => item.volunteer_id === volunteer.id && item.id !== assignment.id && ['assigned', 'in progress'].includes(item.status));
        if (!open && volunteer.availability_status === 'assigned') volunteer.availability_status = 'available';
      }
      return copy({ assignment, volunteer });
    },

    async updateVolunteerAvailability({ availability_status: status }) {
      require(new Set(['Volunteer']));
      const volunteer = ownVolunteer();
      if (!volunteer) throw rejection('No volunteer profile is linked to this account', 404);
      if (['assigned', 'pending verification'].includes(volunteer.availability_status)) {
        throw rejection(`Availability cannot change while the profile is ${volunteer.availability_status}`, 409);
      }
      volunteer.availability_status = status;
      return copy({ volunteer: volunteerPayload() });
    },

    async createNewsUpdate(payload) {
      if (role === 'Citizen') throw rejection('Forbidden for this role', 403);
      const update = { id: nextId(), disaster_id: Number(payload.disaster_id), headline: requiredText(payload, 'headline', 200), summary: requiredText(payload, 'summary', 4000), source_name: requiredText(payload, 'source_name', 120), state: requiredText(payload, 'state', 100), district: requiredText(payload, 'district', 100), stream_url: '', is_live: payload.is_live === true, published_at: timestamp() };
      state.newsUpdates.unshift(update);
      return copy({ news_update: update });
    },

    async createWelfareCheck(payload) {
      if (payload.consent_to_contact !== true) throw rejection('Consent to contact is required');
      const item = { id: nextId(), requester_id: user().id, disaster_id: Number(payload.disaster_id) || null, relative_name: requiredText(payload, 'relative_name', 120), relative_phone: payload.relative_phone || '', relationship: requiredText(payload, 'relationship', 80), last_known_location: requiredText(payload, 'last_known_location', 255), requester_phone: requiredText(payload, 'requester_phone', 30), consent_to_contact: true, status: 'requested', responder_notes: '', created_at: timestamp(), updated_at: timestamp() };
      state.welfareChecks.unshift(item);
      return copy({ welfare_check: item });
    },

    async updateWelfareCheck(id, { status, responder_notes: notes }) {
      require(WELFARE_ROLES);
      const item = find(state.welfareChecks, id, 'Welfare check');
      Object.assign(item, { status, responder_notes: notes ?? item.responder_notes, updated_at: timestamp() });
      return copy({ welfare_check: item });
    },

    async createSupplyRequest(payload) {
      const item = { id: nextId(), requester_id: user().id, disaster_id: Number(payload.disaster_id), category: requiredText(payload, 'category', 60), description: requiredText(payload, 'description', 2000), people_count: Math.max(1, Number(payload.people_count) || 1), urgency: payload.urgency || 'high', contact_phone: requiredText(payload, 'contact_phone', 30), latitude: coordinate(payload.latitude, 'latitude', 90), longitude: coordinate(payload.longitude, 'longitude', 180), status: 'requested', assigned_unit: '', responder_notes: '', created_at: timestamp(), updated_at: timestamp() };
      state.supplyRequests.unshift(item);
      return copy({ supply_request: item, hotline: '112' });
    },

    async updateSupplyRequest(id, payload) {
      require(SUPPLY_ROLES);
      const item = find(state.supplyRequests, id, 'Supply request');
      let unit = item.assigned_unit ? state.responderUnits.find((entry) => entry.name === item.assigned_unit) : null;
      if (payload.assigned_unit && payload.assigned_unit !== item.assigned_unit) {
        const candidate = state.responderUnits.find((entry) => entry.name === payload.assigned_unit);
        if (!candidate) throw rejection('assigned_unit must match a registered responder unit');
        if (candidate.availability_status !== 'available') throw rejection('The selected responder unit is not available', 409);
        if (unit) unit.availability_status = 'available';
        unit = candidate;
        item.assigned_unit = candidate.name;
      }
      item.status = payload.status;
      if (unit) unit.availability_status = ['delivered', 'cancelled'].includes(payload.status) ? 'available' : 'dispatched';
      item.updated_at = timestamp();
      return copy({ supply_request: item, responder_unit: unit || null });
    },

    async acknowledgeHospitalNotification(id) {
      require(new Set(['Admin', 'Hospital']));
      const item = find(state.hospitalNotifications, id, 'Hospital notice');
      if (role === 'Hospital' && item.hospital_id !== facilityId('hospital')) throw rejection('You can acknowledge only notifications for your assigned hospital', 403);
      Object.assign(item, { status: 'acknowledged', acknowledged_at: timestamp() });
      return copy({ hospital_notification: item });
    },

    async createDonation(payload) {
      const campaign = find(state.campaigns, payload.campaign_id, 'Campaign');
      const amount = Number(payload.amount);
      if (!Number.isFinite(amount) || amount < 10 || amount > 10000000) throw rejection('amount must be between 10 and 10000000');
      campaign.pledged_amount += amount;
      const reference = `DEMO-${nextId()}`;
      return { donation: { id: nextId(), campaign_id: campaign.id, amount, reference, status: 'pledged' }, checkout_url: null, payment_required: false, message: 'Demo pledge recorded in this browser only; no payment was taken.' };
    },

    async shareLocation(payload) {
      return { location_ping: { ...payload, id: nextId(), recorded_at: timestamp() } };
    },

    async safeRoute({ latitude, longitude, destination = 'shelter' }) {
      const origin = { latitude: coordinate(latitude, 'latitude', 90), longitude: coordinate(longitude, 'longitude', 180) };
      const candidates = destination === 'hospital' ? state.hospitals.filter((item) => item.available_beds > 0) : state.shelters.filter((item) => item.available_capacity > 0);
      const nearest = nearestItem(origin, candidates);
      if (!nearest) throw rejection(`No available ${destination} found`, 404);
      const hazards = state.disasters.filter((item) => item.status === 'active' && (distanceKm(origin, item) ?? Infinity) < 5);
      return copy({
        destination_type: destination,
        destination: nearest.item,
        distance_km: Number(nearest.distance.toFixed(1)),
        nearby_hazards: hazards,
        guidance: 'Follow official road closures and field-team instructions; the route link is advisory, not a guarantee of road safety.',
        navigation_url: `https://www.google.com/maps/dir/?api=1&origin=${origin.latitude},${origin.longitude}&destination=${nearest.item.latitude},${nearest.item.longitude}&travelmode=driving`,
      });
    },

    async createRoadClosure(payload) {
      require(new Set(['Admin', 'Police', 'Fire Service']));
      const closure = { id: nextId(), disaster_id: Number(payload.disaster_id) || null, road_name: requiredText(payload, 'road_name', 160), location: requiredText(payload, 'location', 255), latitude: coordinate(payload.latitude, 'latitude', 90), longitude: coordinate(payload.longitude, 'longitude', 180), status: payload.status === 'restricted' ? 'restricted' : 'closed', reason: requiredText(payload, 'reason', 500), diversion: String(payload.diversion || ''), reported_by_id: user().id, created_at: timestamp(), updated_at: timestamp() };
      state.roadClosures.unshift(closure);
      return copy({ road_closure: closure });
    },

    async updateRoadClosure(id, payload) {
      require(new Set(['Admin', 'Police', 'Fire Service']));
      const closure = find(state.roadClosures, id, 'Road closure');
      if (payload.status) closure.status = payload.status;
      closure.updated_at = timestamp();
      return copy({ road_closure: closure });
    },

    async createReadinessCheck({ subject, items, notes }) {
      require(READINESS_ROLES);
      const entries = Object.entries(items || {});
      if (!entries.length) throw rejection('Add at least one checklist item');
      const check = { id: nextId(), user_id: user().id, role, subject: requiredText({ subject }, 'subject', 160), items: { ...items }, ready_count: entries.filter(([, done]) => done).length, total_count: entries.length, notes: String(notes || ''), created_at: timestamp() };
      state.readinessChecks.unshift(check);
      return copy({ readiness_check: check });
    },

    async adminUsers() {
      require(new Set(['Admin']));
      return copy({ users: state.users });
    },

    async adminIntegrations() {
      require(new Set(['Admin']));
      const integrations = [
        ['persistent_database', 'Persistent operational database', 'active', 'Demo sandbox: records stay in this browser tab', [], true],
        ['public_alert_delivery', 'External public-warning delivery', 'fallback', 'In-app warnings and acknowledgements only', ['ALERT_DELIVERY_WEBHOOK_URL', 'ALERT_DELIVERY_WEBHOOK_SECRET'], false],
        ['email_recovery', 'Email password recovery', 'fallback', 'Administrator-assisted reset after identity verification', ['PUBLIC_BASE_URL', 'SMTP_HOST', 'SMTP_FROM_EMAIL'], false],
        ['online_donations', 'Hosted donation checkout', 'fallback', 'Auditable pledges only; no money represented as collected', ['DONATION_PAYMENT_URL'], false],
        ['maps', 'Maps and destination guidance', 'active', 'OpenStreetMap browser tiles with typed-coordinate fallback', [], false],
      ].map(([id, name, status, mode, variables, core]) => ({ id, name, status, configured: status === 'active', mode, fallback: mode, activation_variables: variables, required_for_core: core }));
      const active = integrations.filter((item) => item.status === 'active').length;
      return { generated_at: timestamp(), summary: { active, fallback: integrations.length - active, total: integrations.length, external_activation_complete: false }, integrations };
    },

    async provisionUser(payload) {
      require(new Set(['Admin']));
      const email = requiredText(payload, 'email', 160).toLowerCase();
      if (state.users.some((item) => item.email === email)) throw rejection('Email already registered', 409);
      const created = { id: nextId(), name: requiredText(payload, 'name', 120), email, phone: requiredText(payload, 'phone', 30), role: payload.role, organization_name: payload.organization_name || null, is_active: true, verification_status: 'verified', password_change_required: true, created_at: timestamp() };
      state.users.unshift(created);
      return copy({ user: created, facility: null });
    },

    async updateUserAccess(id, payload) {
      require(new Set(['Admin']));
      const target = find(state.users, id, 'User');
      if (payload.verification_status) {
        target.verification_status = payload.verification_status;
        target.is_active = payload.verification_status === 'verified';
        const volunteer = state.volunteers.find((item) => item.user_id === target.id);
        if (volunteer && payload.verification_status === 'verified' && volunteer.availability_status === 'pending verification') {
          volunteer.availability_status = 'available';
        }
      }
      if (typeof payload.is_active === 'boolean') target.is_active = payload.is_active;
      return copy({ user: target });
    },

    async resetUserPassword(id) {
      require(new Set(['Admin']));
      const target = find(state.users, id, 'User');
      target.password_change_required = true;
      return { message: 'Password reset and active sessions revoked' };
    },

    async createResource(payload) {
      require(new Set(['Admin']));
      const resource = { id: nextId(), name: requiredText(payload, 'name', 120), category: requiredText(payload, 'category', 60).toLowerCase(), unit: requiredText(payload, 'unit', 30), available_quantity: Math.max(0, Number(payload.available_quantity) || 0), storage_location: requiredText(payload, 'storage_location', 160) };
      state.resources.push(resource);
      return copy({ resource });
    },

    async createResponder(payload) {
      require(new Set(['Admin']));
      const name = requiredText(payload, 'name', 160);
      if (state.responderUnits.some((item) => item.name === name)) throw rejection('A responder unit with this name already exists', 409);
      const responder = { id: nextId(), name, unit_type: requiredText(payload, 'unit_type', 50), skills: requiredText(payload, 'skills', 255), contact_phone: requiredText(payload, 'contact_phone', 30), latitude: coordinate(payload.latitude, 'latitude', 90), longitude: coordinate(payload.longitude, 'longitude', 180), availability_status: 'available', updated_at: timestamp() };
      state.responderUnits.push(responder);
      return copy({ responder });
    },

    async createDonationCampaign(payload) {
      require(new Set(['Admin']));
      const goal = Number(payload.goal_amount);
      if (!Number.isFinite(goal) || goal <= 0) throw rejection('goal_amount must be greater than zero');
      const campaign = { id: nextId(), disaster_id: Number(payload.disaster_id) || null, title: requiredText(payload, 'title', 180), description: requiredText(payload, 'description', 4000), goal_amount: goal, confirmed_amount: 0, pledged_amount: 0, currency: payload.currency || 'INR', organizer: requiredText(payload, 'organizer', 160), status: 'active' };
      state.campaigns.unshift(campaign);
      return copy({ campaign });
    },
  };
  return client;
}
