USE disaster_response;

INSERT INTO users (name, email, phone, role, password_hash) VALUES
('Incident Commander', 'admin@rescue.local', '9000000000', 'Admin', 'demo-hash'),
('Asha Nair', 'citizen@rescue.local', '9000000001', 'Citizen', 'demo-hash'),
('City Hospital Desk', 'hospital@rescue.local', '9000000002', 'Hospital', 'demo-hash'),
('Relief NGO Coordinator', 'ngo@rescue.local', '9000000003', 'NGO', 'demo-hash');

INSERT INTO disasters (title, disaster_type, description, address, latitude, longitude, people_affected, severity_hint, reported_by_id) VALUES
('Flooding near Riverside Colony', 'flood', 'Water level rising rapidly near low-lying homes.', 'Riverside Colony, Kochi', 9.9312000, 76.2673000, 240, 'high', 2),
('Apartment fire at Market Road', 'fire', 'Smoke and flames reported near market road.', 'Market Road, Ernakulam', 9.9821000, 76.2999000, 65, 'high', 2);

INSERT INTO hospitals (name, address, latitude, longitude, total_beds, available_beds, icu_beds, emergency_capacity, contact_phone) VALUES
('City Emergency Hospital', 'MG Road, Kochi', 9.9668000, 76.2870000, 180, 42, 8, 30, '0484000001'),
('General Hospital Ernakulam', 'Hospital Road, Kochi', 9.9800000, 76.2800000, 220, 24, 3, 20, '0484000002');

INSERT INTO shelters (name, address, latitude, longitude, total_capacity, available_capacity, food_available, medical_support, contact_phone) VALUES
('Govt HSS Relief Camp', 'Panampilly Nagar, Kochi', 9.9515000, 76.2998000, 600, 310, TRUE, TRUE, '0484000003'),
('Community Hall Camp', 'Vyttila, Kochi', 9.9660000, 76.3180000, 220, 86, TRUE, FALSE, '0484000004');

INSERT INTO ambulances (vehicle_number, driver_name, phone, latitude, longitude, status, hospital_id) VALUES
('KL-07-ER-108', 'Nikhil Das', '9000000108', 9.9668000, 76.2870000, 'available', 1),
('KL-07-ER-214', 'Ameena P', '9000000214', 9.9800000, 76.2800000, 'dispatched', 2);

INSERT INTO resources (name, category, unit, available_quantity, storage_location) VALUES
('Food Packets', 'food', 'packet', 2500, 'Central Warehouse'),
('ORS Sachets', 'medicine', 'box', 800, 'Medical Depot'),
('Rescue Boats', 'rescue', 'boat', 12, 'Fire Station Dock');

INSERT INTO rescue_requests (disaster_id, requester_id, victim_name, victim_age, people_count, condition_label, trapped, vulnerable_people, latitude, longitude, status, priority_score, priority_label, assigned_unit, notes) VALUES
(1, 2, 'Maya Joseph', 8, 3, 'critical', TRUE, 1, 9.9320000, 76.2690000, 'assigned', 97, 'Critical', 'Boat Rescue Unit 2', 'Child and two adults on rooftop.'),
(2, 2, 'Suresh Menon', 72, 1, 'injured', FALSE, 1, 9.9810000, 76.3010000, 'pending', 72, 'High', NULL, 'Smoke inhalation; needs ambulance.');
