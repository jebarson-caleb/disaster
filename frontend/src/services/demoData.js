// Fictional sample records for the in-browser demo sandbox. Nothing here is real
// personal or incident data, and none of it is ever sent to the live API.

export const DEMO_USERS = {
  Admin: { id: 1, name: 'Anita Rao', role: 'Admin', email: 'commander@demo.resq.invalid', phone: '+91 90000 00001', organization_name: 'State Emergency Operations Centre' },
  Citizen: { id: 2, name: 'Kavya Raman', role: 'Citizen', email: 'kavya@demo.resq.invalid', phone: '+91 90000 00002', organization_name: null },
  Hospital: { id: 3, name: 'Dr. Suresh Iyer', role: 'Hospital', email: 'er-desk@demo.resq.invalid', phone: '+91 90000 00003', organization_name: 'Rajiv Gandhi Govt General Hospital', managed_facility: { type: 'hospital', id: 1 } },
  Shelter: { id: 4, name: 'Lakshmi Narayanan', role: 'Shelter', email: 'camp-lead@demo.resq.invalid', phone: '+91 90000 00004', organization_name: 'Velachery Relief Camp', managed_facility: { type: 'shelter', id: 1 } },
  Ambulance: { id: 5, name: 'Karthik Raj', role: 'Ambulance', email: 'ambulance-108@demo.resq.invalid', phone: '+91 90000 00005', organization_name: '108 Emergency Services', managed_facility: { type: 'ambulance', id: 1 } },
  NGO: { id: 6, name: 'Priya Das', role: 'NGO', email: 'relief@demo.resq.invalid', phone: '+91 90000 00006', organization_name: 'Coastal Relief Collective' },
  Volunteer: { id: 7, name: 'Ravi Kumar', role: 'Volunteer', email: 'ravi@demo.resq.invalid', phone: '+91 90000 00007', organization_name: 'Civil Defence Volunteers' },
  Police: { id: 8, name: 'Inspector Arjun Menon', role: 'Police', email: 'control-room@demo.resq.invalid', phone: '+91 90000 00008', organization_name: 'Chennai City Police' },
  'Fire Service': { id: 9, name: 'Station Officer Farah Khan', role: 'Fire Service', email: 'fire-control@demo.resq.invalid', phone: '+91 90000 00009', organization_name: 'Tamil Nadu Fire and Rescue Services' },
};

export function createDemoState(now = Date.now()) {
  const ago = (minutes) => new Date(now - minutes * 60000).toISOString();
  const ahead = (minutes) => new Date(now + minutes * 60000).toISOString();

  return {
    nextId: 1000,
    users: [
      ...Object.values(DEMO_USERS).map((user, index) => ({
        ...user,
        is_active: true,
        verification_status: 'verified',
        password_change_required: false,
        created_at: ago(60 * 24 * (30 - index)),
      })),
      { id: 10, name: 'Neha Joshi', role: 'Volunteer', email: 'neha@demo.resq.invalid', phone: '+91 90000 00010', organization_name: 'NSS Volunteer Unit', is_active: false, verification_status: 'pending', password_change_required: false, created_at: ago(90) },
      { id: 11, name: 'Imran Ali', role: 'Volunteer', email: 'imran@demo.resq.invalid', phone: '+91 90000 00011', organization_name: 'Community Kitchen Network', is_active: true, verification_status: 'verified', password_change_required: false, created_at: ago(60 * 24 * 4) },
      { id: 12, name: 'Meera Subramanian', role: 'Volunteer', email: 'meera@demo.resq.invalid', phone: '+91 90000 00012', organization_name: 'Civil Defence Volunteers', is_active: true, verification_status: 'verified', password_change_required: true, created_at: ago(60 * 5) },
    ],
    disasters: [
      { id: 1, title: 'Flooding near Velachery lake bund', disaster_type: 'flood', address: 'Velachery, Chennai, Tamil Nadu', description: 'Lake bund overflow has flooded low-lying streets; water is waist-deep near the canal.', latitude: 12.9798, longitude: 80.2209, people_affected: 320, severity_hint: 'high', status: 'active', score: 91, label: 'Critical', created_at: ago(310) },
      { id: 2, title: 'Cyclone wind damage at Cuddalore coast', disaster_type: 'cyclone', address: 'Devanampattinam, Cuddalore, Tamil Nadu', description: 'Uprooted trees and damaged roofs along the fishing hamlets after landfall.', latitude: 11.7447, longitude: 79.7714, people_affected: 180, severity_hint: 'high', status: 'active', score: 82, label: 'High', created_at: ago(250) },
      { id: 3, title: 'Landslide risk on Nilgiris ghat road', disaster_type: 'landslide', address: 'Coonoor Ghat Road, Nilgiris, Tamil Nadu', description: 'Cracks on the hill slope above hairpin bend 9 after 36 hours of rain.', latitude: 11.353, longitude: 76.7959, people_affected: 46, severity_hint: 'medium', status: 'monitoring', score: 61, label: 'Medium', created_at: ago(190) },
      { id: 4, title: 'Brahmaputra flooding isolates Dibrugarh villages', disaster_type: 'flood', address: 'Dibrugarh, Assam', description: 'Embankment breach has cut road access to six riverine villages.', latitude: 27.4728, longitude: 94.912, people_affected: 1450, severity_hint: 'critical', status: 'active', score: 96, label: 'Critical', created_at: ago(140) },
      { id: 5, title: 'Commercial fire near Dharavi market', disaster_type: 'fire', address: 'Dharavi, Mumbai, Maharashtra', description: 'Fire in a garment workshop cluster; smoke spreading to adjoining homes.', latitude: 19.039, longitude: 72.853, people_affected: 85, severity_hint: 'high', status: 'active', score: 84, label: 'High', created_at: ago(70) },
      { id: 6, title: 'Cyclone watch for Puri coastline', disaster_type: 'cyclone', address: 'Puri, Odisha', description: 'Deep depression expected to intensify; fishing boats recalled.', latitude: 19.8135, longitude: 85.8312, people_affected: 0, severity_hint: 'medium', status: 'monitoring', score: 55, label: 'Medium', created_at: ago(35) },
    ],
    rescues: [
      { id: 101, disaster_id: 1, requester_id: 2, victim_name: 'Meena Kumar', victim_age: 8, people_count: 3, condition: 'critical', trapped: true, vulnerable_people: 1, latitude: 12.9806, longitude: 80.2194, priority_score: 97, priority_label: 'Critical', status: 'assigned', assigned_unit: 'TNDRF Boat Unit 2 + TN-01-ER-108', notes: 'Child and two adults stranded on a first-floor terrace near the canal.', created_at: ago(48), updated_at: ago(40) },
      { id: 102, disaster_id: 2, requester_id: 20, victim_name: 'R. Murugan', victim_age: 72, people_count: 1, condition: 'injured', trapped: false, vulnerable_people: 1, latitude: 11.7461, longitude: 79.7728, priority_score: 72, priority_label: 'High', status: 'pending', assigned_unit: '', notes: 'Tree-fall injury to the leg; needs a stretcher and ambulance.', created_at: ago(36), updated_at: ago(36) },
      { id: 103, disaster_id: 1, requester_id: 21, victim_name: 'Fathima Banu', victim_age: 31, people_count: 5, condition: 'stable', trapped: false, vulnerable_people: 2, latitude: 12.9769, longitude: 80.224, priority_score: 43, priority_label: 'Medium', status: 'en route', assigned_unit: 'Ravi Kumar', notes: 'Family of five needs relocation to the Velachery relief camp.', created_at: ago(95), updated_at: ago(20) },
      { id: 104, disaster_id: 1, requester_id: 2, victim_name: 'Raman household', victim_age: 64, people_count: 4, condition: 'stable', trapped: false, vulnerable_people: 1, latitude: 12.9785, longitude: 80.2231, priority_score: 52, priority_label: 'Medium', status: 'assigned', assigned_unit: 'Chennai Police QRT 1', notes: 'Ground floor flooded; elderly parent uses a walker.', created_at: ago(26), updated_at: ago(18) },
      { id: 105, disaster_id: 5, requester_id: 22, victim_name: 'Sanjay Patil', victim_age: 45, people_count: 2, condition: 'injured', trapped: false, vulnerable_people: 0, latitude: 19.0396, longitude: 72.8525, priority_score: 74, priority_label: 'High', status: 'en route', assigned_unit: 'Mumbai Fire Brigade Unit 7', notes: 'Smoke inhalation; workers sheltering on the roof of the adjacent building.', created_at: ago(55), updated_at: ago(15) },
      { id: 106, disaster_id: 4, requester_id: 23, victim_name: 'Majuli Char village cluster', victim_age: 0, people_count: 18, condition: 'stable', trapped: true, vulnerable_people: 6, latitude: 27.4802, longitude: 94.9255, priority_score: 81, priority_label: 'High', status: 'pending', assigned_unit: '', notes: 'Eighteen residents on the school roof; boat access only.', created_at: ago(30), updated_at: ago(30) },
      { id: 107, disaster_id: 3, requester_id: 24, victim_name: 'Lalitha Devi', victim_age: 70, people_count: 1, condition: 'injured', trapped: false, vulnerable_people: 1, latitude: 11.3561, longitude: 76.7942, priority_score: 66, priority_label: 'High', status: 'rescued', assigned_unit: 'TN-38-ER-443', notes: 'Fall injury during evacuation; handed over to Coonoor GH.', created_at: ago(170), updated_at: ago(45) },
    ],
    hospitals: [
      { id: 1, name: 'Rajiv Gandhi Govt General Hospital', address: 'Park Town, Chennai', latitude: 13.0816, longitude: 80.2761, total_beds: 220, available_beds: 52, icu_beds: 10, emergency_capacity: 36, contact_phone: '044-2530-5000', updated_at: ago(25) },
      { id: 2, name: 'Stanley Medical College Hospital', address: 'Old Washermanpet, Chennai', latitude: 13.1067, longitude: 80.287, total_beds: 260, available_beds: 31, icu_beds: 6, emergency_capacity: 24, contact_phone: '044-2528-1351', updated_at: ago(60) },
      { id: 3, name: 'Cuddalore Govt Medical College Hospital', address: 'Cuddalore', latitude: 11.748, longitude: 79.75, total_beds: 180, available_beds: 28, icu_beds: 4, emergency_capacity: 18, contact_phone: '04142-230-500', updated_at: ago(80) },
      { id: 4, name: 'KEM Hospital', address: 'Parel, Mumbai', latitude: 19.0028, longitude: 72.8423, total_beds: 400, available_beds: 64, icu_beds: 12, emergency_capacity: 40, contact_phone: '022-2410-7000', updated_at: ago(30) },
    ],
    shelters: [
      { id: 1, name: 'Velachery Govt School Relief Camp', address: 'Velachery, Chennai', latitude: 12.9822, longitude: 80.2218, total_capacity: 700, available_capacity: 420, food_available: true, medical_support: true, contact_phone: '044-2243-1000', updated_at: ago(15) },
      { id: 2, name: 'Cuddalore Cyclone Shelter', address: 'Devanampattinam, Cuddalore', latitude: 11.75, longitude: 79.77, total_capacity: 360, available_capacity: 190, food_available: true, medical_support: true, contact_phone: '04142-220-100', updated_at: ago(50) },
      { id: 3, name: 'Coonoor Community Hall Camp', address: 'Coonoor, Nilgiris', latitude: 11.3536, longitude: 76.795, total_capacity: 160, available_capacity: 74, food_available: true, medical_support: false, contact_phone: '0423-223-0100', updated_at: ago(120) },
      { id: 4, name: 'Dibrugarh Higher Secondary Relief Camp', address: 'Dibrugarh, Assam', latitude: 27.48, longitude: 94.91, total_capacity: 900, available_capacity: 260, food_available: false, medical_support: true, contact_phone: '0373-232-0100', updated_at: ago(40) },
    ],
    ambulances: [
      { id: 1, vehicle_number: 'TN-01-ER-108', driver_name: 'Karthik Raj', phone: '+91 90000 00108', latitude: 13.0012, longitude: 80.2412, status: 'dispatched', hospital_id: 1, updated_at: ago(10) },
      { id: 2, vehicle_number: 'TN-31-ER-214', driver_name: 'Ameena Begum', phone: '+91 90000 00214', latitude: 11.7521, longitude: 79.7604, status: 'available', hospital_id: 3, updated_at: ago(35) },
      { id: 3, vehicle_number: 'TN-38-ER-443', driver_name: 'Prakash Selvam', phone: '+91 90000 00443', latitude: 11.351, longitude: 76.798, status: 'available', hospital_id: null, updated_at: ago(45) },
      { id: 4, vehicle_number: 'MH-01-ER-777', driver_name: 'Vikas Shinde', phone: '+91 90000 00777', latitude: 19.0101, longitude: 72.8452, status: 'maintenance', hospital_id: 4, updated_at: ago(90) },
    ],
    responderUnits: [
      { id: 1, name: 'TNDRF Boat Unit 2', unit_type: 'water rescue', skills: 'boats, swift-water rescue, first aid', contact_phone: '+91 90000 01001', latitude: 12.9902, longitude: 80.2183, availability_status: 'dispatched', updated_at: ago(40) },
      { id: 2, name: 'Chennai Fire Rescue Tender 3', unit_type: 'fire rescue', skills: 'extrication, breathing apparatus, ladders', contact_phone: '+91 90000 01002', latitude: 13.0108, longitude: 80.2337, availability_status: 'available', updated_at: ago(60) },
      { id: 3, name: 'NDRF 4th Battalion Team B', unit_type: 'professional rescue', skills: 'collapsed structures, boats, relief logistics', contact_phone: '+91 90000 01003', latitude: 11.7608, longitude: 79.7601, availability_status: 'dispatched', updated_at: ago(25) },
      { id: 4, name: 'Mumbai Fire Brigade Unit 7', unit_type: 'fire rescue', skills: 'fire suppression, rope rescue, breathing apparatus', contact_phone: '+91 90000 01004', latitude: 19.0412, longitude: 72.8561, availability_status: 'dispatched', updated_at: ago(15) },
      { id: 5, name: 'Chennai Police QRT 1', unit_type: 'police', skills: 'crowd control, traffic diversion, evacuation', contact_phone: '+91 90000 01005', latitude: 12.9875, longitude: 80.2226, availability_status: 'dispatched', updated_at: ago(18) },
      { id: 6, name: 'Assam SDRF Boat Team 1', unit_type: 'water rescue', skills: 'boats, swift-water rescue, relief logistics', contact_phone: '+91 90000 01006', latitude: 27.4691, longitude: 94.9032, availability_status: 'available', updated_at: ago(50) },
    ],
    volunteers: [
      { id: 1, user_id: 7, name: 'Ravi Kumar', skills: 'first aid, evacuation, logistics', availability_status: 'assigned', latitude: 12.982, longitude: 80.222 },
      { id: 2, user_id: 12, name: 'Meera Subramanian', skills: 'shelter intake, child care, translation', availability_status: 'available', latitude: 12.9901, longitude: 80.2302 },
      { id: 3, user_id: 11, name: 'Imran Ali', skills: 'community kitchen, logistics, driving', availability_status: 'available', latitude: 11.7502, longitude: 79.7699 },
      { id: 4, user_id: 10, name: 'Neha Joshi', skills: 'first aid, counselling', availability_status: 'pending verification', latitude: 13.04, longitude: 80.25 },
    ],
    volunteerAssignments: [
      { id: 1, volunteer_id: 1, disaster_id: 1, task: 'Escort the Banu family from the canal road to the Velachery relief camp', status: 'assigned', assigned_at: ago(22) },
      { id: 2, volunteer_id: 3, disaster_id: 2, task: 'Run the evening meal line at the Cuddalore cyclone shelter', status: 'completed', assigned_at: ago(300) },
    ],
    dispatches: [
      { id: 1, rescue_request_id: 101, responder_type: 'rescue_unit', responder_id: 1, responder_name: 'TNDRF Boat Unit 2', distance_km: 1.1, status: 'assigned', created_at: ago(40) },
      { id: 2, rescue_request_id: 101, responder_type: 'ambulance', responder_id: 1, responder_name: 'TN-01-ER-108', distance_km: 4.2, status: 'assigned', created_at: ago(40) },
      { id: 3, rescue_request_id: 103, responder_type: 'volunteer', responder_id: 1, responder_name: 'Ravi Kumar', distance_km: 0.6, status: 'assigned', created_at: ago(22) },
      { id: 4, rescue_request_id: 104, responder_type: 'rescue_unit', responder_id: 5, responder_name: 'Chennai Police QRT 1', distance_km: 1.0, status: 'assigned', created_at: ago(18) },
      { id: 5, rescue_request_id: 105, responder_type: 'rescue_unit', responder_id: 4, responder_name: 'Mumbai Fire Brigade Unit 7', distance_km: 0.3, status: 'assigned', created_at: ago(15) },
      { id: 6, rescue_request_id: 107, responder_type: 'ambulance', responder_id: 3, responder_name: 'TN-38-ER-443', distance_km: 0.5, status: 'completed', created_at: ago(160) },
    ],
    hospitalNotifications: [
      { id: 1, hospital_id: 1, disaster_id: 1, rescue_request_id: 101, expected_patients: 3, priority: 'Critical', message: 'Prepare for 3 incoming patient(s) from Flooding near Velachery lake bund. Condition: critical.', status: 'sent', created_at: ago(40) },
      { id: 2, hospital_id: 1, disaster_id: 1, rescue_request_id: 104, expected_patients: 1, priority: 'Medium', message: 'Prepare for 1 incoming patient from Flooding near Velachery lake bund. Elderly patient with mobility support needs.', status: 'acknowledged', created_at: ago(18), acknowledged_at: ago(12) },
      { id: 3, hospital_id: 3, disaster_id: 2, rescue_request_id: 102, expected_patients: 1, priority: 'High', message: 'Prepare for 1 incoming patient from Cyclone wind damage at Cuddalore coast. Condition: injured.', status: 'sent', created_at: ago(30) },
    ],
    alerts: [
      { id: 1, identifier: 'RESQ-DEMO-FLOOD-001', event: 'Urban flood warning', audience: 'Ward 176 - Velachery, Chennai', channels: 'SMS + radio + volunteer relay', urgency: 'immediate', severity: 'severe', certainty: 'observed', message: 'Water is rising near the lake bund service road. Low-lying streets will flood further tonight.', instruction: 'Move to Velachery Govt School Relief Camp and avoid the lake bund service road.', status: 'active', delivery_status: 'delivered', delivery_attempts: 1, acknowledgement_count: 214, acknowledged: false, created_at: ago(45), expires_at: ahead(300) },
      { id: 2, identifier: 'RESQ-DEMO-CYCLONE-002', event: 'Cyclone aftermath advisory', audience: 'Cuddalore coastal hamlets', channels: 'SMS + siren', urgency: 'expected', severity: 'moderate', certainty: 'likely', message: 'Fallen power lines reported along East Coast Road.', instruction: 'Stay indoors until TANGEDCO crews clear the lines; report sparks to 112.', status: 'active', delivery_status: 'failed', delivery_attempts: 1, acknowledgement_count: 63, acknowledged: false, created_at: ago(120), expires_at: ahead(240) },
      { id: 3, identifier: 'RESQ-DEMO-FLOOD-003', event: 'River flood warning', audience: 'Dibrugarh riverine villages', channels: 'Radio + village volunteers', urgency: 'immediate', severity: 'extreme', certainty: 'observed', message: 'Brahmaputra is above the danger mark and rising.', instruction: 'Move livestock and family to the relief camp on higher ground before nightfall.', status: 'active', delivery_status: 'not_configured', delivery_attempts: 0, acknowledgement_count: 41, acknowledged: false, created_at: ago(130), expires_at: ahead(600) },
    ],
    newsUpdates: [
      { id: 1, disaster_id: 1, headline: 'Rescue boats enter isolated Velachery streets', summary: 'Verified field teams are moving food, water and residents through the flood corridor.', source_name: 'ResQ verified field desk', state: 'Tamil Nadu', district: 'Chennai', is_live: true, stream_url: '', published_at: ago(20) },
      { id: 2, disaster_id: 4, headline: 'Embankment repair begins at Dibrugarh breach', summary: 'Water Resources Department crews are placing sandbags; road access is still cut.', source_name: 'District Disaster Management Authority', state: 'Assam', district: 'Dibrugarh', is_live: false, stream_url: '', published_at: ago(65) },
      { id: 3, disaster_id: 5, headline: 'Dharavi fire contained to two structures', summary: 'Fire brigade reports the blaze is contained; cooling operations continue.', source_name: 'Mumbai Fire Brigade', state: 'Maharashtra', district: 'Mumbai', is_live: false, stream_url: '', published_at: ago(12) },
    ],
    welfareChecks: [
      { id: 1, requester_id: 2, disaster_id: 1, relative_name: 'Sundar Raman', relative_phone: '+91 90000 00031', relationship: 'Brother', last_known_location: 'Taramani Link Road, Chennai', requester_phone: '+91 90000 00002', consent_to_contact: true, status: 'contacting', responder_notes: 'Volunteer desk calling the last known workplace.', created_at: ago(80), updated_at: ago(30) },
      { id: 2, requester_id: 25, disaster_id: 4, relative_name: 'Bimala Gogoi', relative_phone: '', relationship: 'Mother', last_known_location: 'Majuli Char village, Dibrugarh', requester_phone: '+91 90000 00032', consent_to_contact: true, status: 'requested', responder_notes: '', created_at: ago(28), updated_at: ago(28) },
    ],
    supplyRequests: [
      { id: 1, requester_id: 2, disaster_id: 1, category: 'food and water', description: 'Drinking water and dry rations for 4 people; ground floor flooded.', people_count: 4, urgency: 'high', contact_phone: '+91 90000 00002', latitude: 12.9785, longitude: 80.2231, status: 'requested', assigned_unit: '', responder_notes: '', created_at: ago(25), updated_at: ago(25) },
      { id: 2, requester_id: 26, disaster_id: 2, category: 'medicine', description: 'Insulin and glucose strips for a diabetic resident.', people_count: 1, urgency: 'critical', contact_phone: '+91 90000 00033', latitude: 11.7488, longitude: 79.7699, status: 'packing', assigned_unit: 'NDRF 4th Battalion Team B', responder_notes: 'Packed at Cuddalore GH pharmacy.', created_at: ago(70), updated_at: ago(25) },
      { id: 3, requester_id: 27, disaster_id: 4, category: 'baby supplies', description: 'Infant formula and diapers for 3 infants at the school roof.', people_count: 3, urgency: 'high', contact_phone: '+91 90000 00034', latitude: 27.4802, longitude: 94.9255, status: 'delivered', assigned_unit: 'Assam SDRF Boat Team 1', responder_notes: 'Delivered by boat.', created_at: ago(200), updated_at: ago(110) },
    ],
    campaigns: [
      { id: 1, disaster_id: null, title: 'National Emergency Rescue & Victim Relief Fund', description: 'Supports verified rescue transport, food, medical supplies and recovery assistance.', goal_amount: 2500000, confirmed_amount: 845000, pledged_amount: 120000, currency: 'INR', organizer: 'State Emergency Operations Centre', status: 'active' },
      { id: 2, disaster_id: 4, title: 'Assam Flood Family Kits', description: 'Family kits with tarpaulin, utensils, hygiene supplies and dry rations.', goal_amount: 900000, confirmed_amount: 212000, pledged_amount: 45000, currency: 'INR', organizer: 'Coastal Relief Collective', status: 'active' },
    ],
    resources: [
      { id: 1, name: 'Rice meal packets', category: 'food', unit: 'packet', available_quantity: 3200, storage_location: 'Chennai Corporation Warehouse' },
      { id: 2, name: 'Drinking water (20 L cans)', category: 'water', unit: 'can', available_quantity: 1450, storage_location: 'Guindy Relief Depot' },
      { id: 3, name: 'ORS sachets', category: 'medicine', unit: 'box', available_quantity: 960, storage_location: 'Rajiv Gandhi Medical Depot' },
      { id: 4, name: 'First-aid kits', category: 'medical', unit: 'kit', available_quantity: 210, storage_location: 'Red Cross Store, Egmore' },
      { id: 5, name: 'Tarpaulin sheets', category: 'shelter', unit: 'sheet', available_quantity: 640, storage_location: 'Cuddalore Taluk Store' },
      { id: 6, name: 'Inflatable rescue boats', category: 'rescue', unit: 'boat', available_quantity: 14, storage_location: 'TNDRF Boat Yard' },
    ],
    distributions: [
      { id: 1, resource_id: 1, disaster_id: 1, quantity: 400, destination: 'Velachery Govt School Relief Camp', status: 'delivered', created_at: ago(150) },
      { id: 2, resource_id: 2, disaster_id: 1, quantity: 120, destination: 'Velachery Govt School Relief Camp', status: 'in transit', created_at: ago(35) },
    ],
    roadClosures: [
      { id: 1, disaster_id: 1, road_name: 'Lake bund service road', location: 'Velachery lake bund, Chennai', latitude: 12.9794, longitude: 80.2201, status: 'closed', reason: 'Waist-deep water and a breached drain cover.', diversion: 'Use Velachery Main Road via Vijayanagar junction', reported_by_id: 8, created_at: ago(120), updated_at: ago(40) },
      { id: 2, disaster_id: 2, road_name: 'East Coast Road (Devanampattinam stretch)', location: 'Cuddalore', latitude: 11.7463, longitude: 79.7741, status: 'restricted', reason: 'Fallen trees partially cleared; emergency vehicles only.', diversion: 'Light vehicles via Cuddalore bypass', reported_by_id: 9, created_at: ago(200), updated_at: ago(60) },
      { id: 3, disaster_id: 3, road_name: 'Coonoor Ghat Road, hairpin 9', location: 'Nilgiris', latitude: 11.3518, longitude: 76.7987, status: 'closed', reason: 'Active slope movement above the carriageway.', diversion: 'Kotagiri route', reported_by_id: 8, created_at: ago(180), updated_at: ago(180) },
    ],
    readinessChecks: [
      { id: 1, user_id: 9, role: 'Fire Service', subject: 'Chennai Fire Rescue Tender 3', items: { 'Breathing apparatus (SCBA) charged': true, 'Rescue boat and life jackets': true, 'Rope, harness and throw bags': true, 'Hydraulic extrication tools': false, 'Crew PPE complete': true }, ready_count: 4, total_count: 5, notes: 'Hydraulic cutter hose replacement requested.', created_at: ago(55) },
      { id: 2, user_id: 5, role: 'Ambulance', subject: 'TN-01-ER-108', items: { 'Oxygen cylinders full': true, 'Defibrillator charged': true, 'Stretcher and spine board': true, 'Trauma and burns kit stocked': true, 'Fuel above half tank': true }, ready_count: 5, total_count: 5, notes: '', created_at: ago(70) },
      { id: 3, user_id: 3, role: 'Hospital', subject: 'Emergency department - night shift', items: { 'Triage desk staffed': true, 'Surge ward opened': true, 'Blood bank stock checked': false, 'Generator fuel for 24 hours': true, 'Inter-facility transfer plan confirmed': true }, ready_count: 4, total_count: 5, notes: 'O-negative stock low; requested from Stanley.', created_at: ago(90) },
    ],
    acknowledgedAlertIds: [],
  };
}
