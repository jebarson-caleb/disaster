USE disaster_response;

INSERT INTO users (name, email, phone, role, password_hash) VALUES
('Incident Commander', 'admin@rescue.local', '9000000000', 'Admin', 'demo-hash'),
('Kavya Raman', 'citizen@rescue.local', '9000000001', 'Citizen', 'demo-hash'),
('Chennai Hospital Desk', 'hospital@rescue.local', '9000000002', 'Hospital', 'demo-hash'),
('Relief NGO Coordinator', 'ngo@rescue.local', '9000000003', 'NGO', 'demo-hash');

INSERT INTO disasters (title, disaster_type, description, address, latitude, longitude, people_affected, severity_hint, reported_by_id) VALUES
('Flooding near Velachery lake bund', 'flood', 'Water level rising rapidly near low-lying streets and canals.', 'Velachery, Chennai', 12.9798000, 80.2209000, 320, 'high', 2),
('Cyclone wind damage at Cuddalore coast', 'cyclone', 'Strong wind, tree fall and roof damage reported near the coast.', 'Devanampattinam, Cuddalore', 11.7447000, 79.7714000, 180, 'high', 2);

INSERT INTO hospitals (name, address, latitude, longitude, total_beds, available_beds, icu_beds, emergency_capacity, contact_phone) VALUES
('Rajiv Gandhi Govt General Hospital', 'Park Town, Chennai', 13.0816000, 80.2761000, 220, 52, 10, 36, '0440000001'),
('Stanley Medical College Hospital', 'Old Washermanpet, Chennai', 13.1075000, 80.2866000, 260, 31, 6, 24, '0440000002');

INSERT INTO shelters (name, address, latitude, longitude, total_capacity, available_capacity, food_available, medical_support, contact_phone) VALUES
('Velachery Govt School Relief Camp', 'Velachery, Chennai', 12.9822000, 80.2218000, 700, 420, TRUE, TRUE, '0440000003'),
('Cuddalore Cyclone Shelter', 'Devanampattinam, Cuddalore', 11.7461000, 79.7730000, 360, 190, TRUE, TRUE, '04142000004');

INSERT INTO ambulances (vehicle_number, driver_name, phone, latitude, longitude, status, hospital_id) VALUES
('TN-01-ER-108', 'Karthik Raj', '9000000108', 13.0816000, 80.2761000, 'available', 1),
('TN-31-ER-214', 'Ameena Begum', '9000000214', 11.7461000, 79.7730000, 'dispatched', 2);

INSERT INTO resources (name, category, unit, available_quantity, storage_location) VALUES
('Rice Meal Packets', 'food', 'packet', 3200, 'Chennai Corporation Warehouse'),
('ORS Sachets', 'medicine', 'box', 960, 'Rajiv Gandhi Medical Depot'),
('Rescue Boats', 'rescue', 'boat', 14, 'TNDRF Boat Yard');

INSERT INTO rescue_requests (disaster_id, requester_id, victim_name, victim_age, people_count, condition_label, trapped, vulnerable_people, latitude, longitude, status, priority_score, priority_label, assigned_unit, notes) VALUES
(1, 2, 'Meena Kumar', 8, 3, 'critical', TRUE, 1, 12.9806000, 80.2194000, 'assigned', 97, 'Critical', 'TNDRF Boat Unit 2', 'Child and two adults stranded on first-floor terrace near the canal.'),
(2, 2, 'R. Murugan', 72, 1, 'injured', FALSE, 1, 11.7461000, 79.7728000, 'pending', 72, 'High', NULL, 'Tree fall injury; needs 108 ambulance and stretcher support.');
