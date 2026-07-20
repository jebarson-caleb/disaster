CREATE DATABASE IF NOT EXISTS disaster_response;
USE disaster_response;

CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  email VARCHAR(160) NOT NULL UNIQUE,
  phone VARCHAR(30) NOT NULL,
  role ENUM('Citizen','NGO','Volunteer','Police','Hospital','Fire Service','Shelter','Ambulance','Admin') NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_users_role (role)
);

CREATE TABLE role_profiles (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  organization_name VARCHAR(160),
  address VARCHAR(255),
  latitude DECIMAL(10, 7),
  longitude DECIMAL(10, 7),
  verification_status ENUM('pending','verified','rejected') NOT NULL DEFAULT 'pending',
  CONSTRAINT fk_profiles_user FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE disasters (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(160) NOT NULL,
  disaster_type ENUM('flood','earthquake','cyclone','landslide','fire','other') NOT NULL,
  description TEXT NOT NULL,
  address VARCHAR(255) NOT NULL,
  latitude DECIMAL(10, 7) NOT NULL,
  longitude DECIMAL(10, 7) NOT NULL,
  people_affected INT NOT NULL DEFAULT 0,
  severity_hint ENUM('low','medium','high','critical') NOT NULL DEFAULT 'medium',
  status ENUM('active','monitoring','resolved') NOT NULL DEFAULT 'active',
  image_url VARCHAR(500),
  reported_by_id INT,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_disasters_reporter FOREIGN KEY (reported_by_id) REFERENCES users(id),
  INDEX idx_disasters_type (disaster_type),
  INDEX idx_disasters_status_time (status, created_at),
  INDEX idx_disasters_location (latitude, longitude)
);

CREATE TABLE rescue_requests (
  id INT AUTO_INCREMENT PRIMARY KEY,
  disaster_id INT NOT NULL,
  requester_id INT,
  victim_name VARCHAR(120) NOT NULL,
  victim_age INT NOT NULL DEFAULT 0,
  people_count INT NOT NULL DEFAULT 1,
  condition_label VARCHAR(80) NOT NULL DEFAULT 'stable',
  trapped BOOLEAN NOT NULL DEFAULT FALSE,
  vulnerable_people INT NOT NULL DEFAULT 0,
  notes TEXT,
  latitude DECIMAL(10, 7) NOT NULL,
  longitude DECIMAL(10, 7) NOT NULL,
  status ENUM('pending','assigned','en route','rescued','closed','cancelled') NOT NULL DEFAULT 'pending',
  priority_score INT NOT NULL DEFAULT 0,
  priority_label ENUM('Low','Medium','High','Critical') NOT NULL DEFAULT 'Low',
  assigned_unit VARCHAR(120),
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_rescue_disaster FOREIGN KEY (disaster_id) REFERENCES disasters(id),
  CONSTRAINT fk_rescue_requester FOREIGN KEY (requester_id) REFERENCES users(id),
  INDEX idx_rescue_status_priority (status, priority_score),
  INDEX idx_rescue_disaster (disaster_id),
  INDEX idx_rescue_location (latitude, longitude)
);

CREATE TABLE rescue_status_history (
  id INT AUTO_INCREMENT PRIMARY KEY,
  rescue_request_id INT NOT NULL,
  status VARCHAR(40) NOT NULL,
  note TEXT,
  changed_by_id INT,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_history_rescue FOREIGN KEY (rescue_request_id) REFERENCES rescue_requests(id),
  CONSTRAINT fk_history_user FOREIGN KEY (changed_by_id) REFERENCES users(id),
  INDEX idx_history_rescue (rescue_request_id)
);

CREATE TABLE hospitals (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(160) NOT NULL,
  address VARCHAR(255) NOT NULL,
  latitude DECIMAL(10, 7) NOT NULL,
  longitude DECIMAL(10, 7) NOT NULL,
  total_beds INT NOT NULL,
  available_beds INT NOT NULL,
  icu_beds INT NOT NULL DEFAULT 0,
  emergency_capacity INT NOT NULL DEFAULT 0,
  contact_phone VARCHAR(30) NOT NULL,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_hospitals_capacity (available_beds, emergency_capacity)
);

CREATE TABLE hospital_capacity_logs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  hospital_id INT NOT NULL,
  available_beds INT NOT NULL,
  icu_beds INT NOT NULL,
  emergency_capacity INT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_hospital_logs_hospital FOREIGN KEY (hospital_id) REFERENCES hospitals(id)
);

CREATE TABLE shelters (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(160) NOT NULL,
  address VARCHAR(255) NOT NULL,
  latitude DECIMAL(10, 7) NOT NULL,
  longitude DECIMAL(10, 7) NOT NULL,
  total_capacity INT NOT NULL,
  available_capacity INT NOT NULL,
  food_available BOOLEAN NOT NULL DEFAULT TRUE,
  medical_support BOOLEAN NOT NULL DEFAULT FALSE,
  contact_phone VARCHAR(30) NOT NULL,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_shelters_capacity (available_capacity)
);

CREATE TABLE shelter_capacity_logs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  shelter_id INT NOT NULL,
  available_capacity INT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_shelter_logs_shelter FOREIGN KEY (shelter_id) REFERENCES shelters(id)
);

CREATE TABLE ambulances (
  id INT AUTO_INCREMENT PRIMARY KEY,
  vehicle_number VARCHAR(40) NOT NULL UNIQUE,
  driver_name VARCHAR(120) NOT NULL,
  phone VARCHAR(30) NOT NULL,
  latitude DECIMAL(10, 7) NOT NULL,
  longitude DECIMAL(10, 7) NOT NULL,
  status ENUM('available','dispatched','maintenance','offline') NOT NULL DEFAULT 'available',
  hospital_id INT,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_ambulance_hospital FOREIGN KEY (hospital_id) REFERENCES hospitals(id),
  INDEX idx_ambulance_status (status)
);

CREATE TABLE ambulance_dispatches (
  id INT AUTO_INCREMENT PRIMARY KEY,
  ambulance_id INT NOT NULL,
  rescue_request_id INT NOT NULL,
  status ENUM('dispatched','arrived','completed','cancelled') NOT NULL DEFAULT 'dispatched',
  dispatched_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_dispatch_ambulance FOREIGN KEY (ambulance_id) REFERENCES ambulances(id),
  CONSTRAINT fk_dispatch_rescue FOREIGN KEY (rescue_request_id) REFERENCES rescue_requests(id)
);

CREATE TABLE resources (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  category ENUM('food','medicine','rescue','shelter','water','other') NOT NULL,
  unit VARCHAR(30) NOT NULL,
  available_quantity INT NOT NULL DEFAULT 0,
  storage_location VARCHAR(160) NOT NULL,
  INDEX idx_resources_category (category)
);

CREATE TABLE resource_distribution (
  id INT AUTO_INCREMENT PRIMARY KEY,
  resource_id INT NOT NULL,
  disaster_id INT NOT NULL,
  quantity INT NOT NULL,
  destination VARCHAR(180) NOT NULL,
  status ENUM('planned','dispatched','delivered','cancelled') NOT NULL DEFAULT 'planned',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_distribution_resource FOREIGN KEY (resource_id) REFERENCES resources(id),
  CONSTRAINT fk_distribution_disaster FOREIGN KEY (disaster_id) REFERENCES disasters(id)
);

CREATE TABLE volunteers (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  skills VARCHAR(255) NOT NULL,
  availability_status ENUM('available','assigned','offline') NOT NULL DEFAULT 'available',
  latitude DECIMAL(10, 7),
  longitude DECIMAL(10, 7),
  CONSTRAINT fk_volunteer_user FOREIGN KEY (user_id) REFERENCES users(id),
  INDEX idx_volunteer_availability (availability_status)
);

CREATE TABLE volunteer_assignments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  volunteer_id INT NOT NULL,
  disaster_id INT NOT NULL,
  task VARCHAR(180) NOT NULL,
  status ENUM('assigned','in progress','completed','cancelled') NOT NULL DEFAULT 'assigned',
  assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_assignment_volunteer FOREIGN KEY (volunteer_id) REFERENCES volunteers(id),
  CONSTRAINT fk_assignment_disaster FOREIGN KEY (disaster_id) REFERENCES disasters(id)
);

CREATE TABLE ai_assessments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  entity_type VARCHAR(40) NOT NULL,
  entity_id INT NOT NULL,
  assessment_type VARCHAR(60) NOT NULL,
  score INT NOT NULL,
  label VARCHAR(40) NOT NULL,
  explanation TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_ai_entity (entity_type, entity_id)
);

CREATE TABLE notifications (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT,
  role VARCHAR(40),
  message TEXT NOT NULL,
  status ENUM('unread','read') NOT NULL DEFAULT 'unread',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_notifications_user FOREIGN KEY (user_id) REFERENCES users(id),
  INDEX idx_notifications_role (role, status)
);

CREATE TABLE emergency_alerts (
  id INT AUTO_INCREMENT PRIMARY KEY,
  identifier VARCHAR(80) NOT NULL UNIQUE,
  sender_id INT NOT NULL,
  event VARCHAR(100) NOT NULL,
  audience VARCHAR(180) NOT NULL,
  channels VARCHAR(180) NOT NULL,
  urgency VARCHAR(30) NOT NULL DEFAULT 'immediate',
  severity VARCHAR(30) NOT NULL DEFAULT 'severe',
  certainty VARCHAR(30) NOT NULL DEFAULT 'likely',
  message TEXT NOT NULL,
  instruction TEXT NOT NULL,
  status VARCHAR(30) NOT NULL DEFAULT 'active',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMP NULL,
  CONSTRAINT fk_alert_sender FOREIGN KEY (sender_id) REFERENCES users(id),
  INDEX idx_alert_audience (audience),
  INDEX idx_alert_status_time (status, created_at)
);

CREATE TABLE alert_acknowledgements (
  id INT AUTO_INCREMENT PRIMARY KEY,
  alert_id INT NOT NULL,
  user_id INT NOT NULL,
  response VARCHAR(30) NOT NULL DEFAULT 'received',
  latitude DECIMAL(10, 7),
  longitude DECIMAL(10, 7),
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_ack_alert FOREIGN KEY (alert_id) REFERENCES emergency_alerts(id),
  CONSTRAINT fk_ack_user FOREIGN KEY (user_id) REFERENCES users(id),
  CONSTRAINT uq_alert_user_ack UNIQUE (alert_id, user_id)
);

CREATE TABLE disaster_news_updates (
  id INT AUTO_INCREMENT PRIMARY KEY,
  disaster_id INT NOT NULL,
  headline VARCHAR(200) NOT NULL,
  summary TEXT NOT NULL,
  source_name VARCHAR(120) NOT NULL,
  stream_url VARCHAR(500),
  state VARCHAR(100) NOT NULL,
  district VARCHAR(100) NOT NULL,
  is_live BOOLEAN NOT NULL DEFAULT FALSE,
  is_verified BOOLEAN NOT NULL DEFAULT TRUE,
  published_by_id INT,
  published_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_news_disaster FOREIGN KEY (disaster_id) REFERENCES disasters(id),
  CONSTRAINT fk_news_publisher FOREIGN KEY (published_by_id) REFERENCES users(id),
  INDEX idx_news_location_live (state, district, is_live),
  INDEX idx_news_disaster_time (disaster_id, published_at)
);

CREATE TABLE welfare_checks (
  id INT AUTO_INCREMENT PRIMARY KEY,
  requester_id INT NOT NULL,
  disaster_id INT,
  relative_name VARCHAR(120) NOT NULL,
  relative_phone VARCHAR(30),
  relationship VARCHAR(80) NOT NULL,
  last_known_location VARCHAR(255) NOT NULL,
  latitude DECIMAL(10, 7),
  longitude DECIMAL(10, 7),
  requester_phone VARCHAR(30) NOT NULL,
  consent_to_contact BOOLEAN NOT NULL DEFAULT FALSE,
  status VARCHAR(40) NOT NULL DEFAULT 'requested',
  responder_id INT,
  responder_notes TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_welfare_requester FOREIGN KEY (requester_id) REFERENCES users(id),
  CONSTRAINT fk_welfare_disaster FOREIGN KEY (disaster_id) REFERENCES disasters(id),
  CONSTRAINT fk_welfare_responder FOREIGN KEY (responder_id) REFERENCES users(id),
  INDEX idx_welfare_status_time (status, created_at),
  INDEX idx_welfare_name (relative_name)
);

CREATE TABLE hospital_notifications (
  id INT AUTO_INCREMENT PRIMARY KEY,
  hospital_id INT NOT NULL,
  disaster_id INT NOT NULL,
  rescue_request_id INT NOT NULL,
  expected_patients INT NOT NULL DEFAULT 1,
  priority VARCHAR(30) NOT NULL,
  message TEXT NOT NULL,
  status VARCHAR(30) NOT NULL DEFAULT 'sent',
  acknowledged_by_id INT,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  acknowledged_at TIMESTAMP NULL,
  CONSTRAINT fk_hospital_notice_hospital FOREIGN KEY (hospital_id) REFERENCES hospitals(id),
  CONSTRAINT fk_hospital_notice_disaster FOREIGN KEY (disaster_id) REFERENCES disasters(id),
  CONSTRAINT fk_hospital_notice_rescue FOREIGN KEY (rescue_request_id) REFERENCES rescue_requests(id),
  CONSTRAINT fk_hospital_notice_user FOREIGN KEY (acknowledged_by_id) REFERENCES users(id),
  INDEX idx_hospital_notice_status (hospital_id, status, created_at)
);

CREATE TABLE supply_requests (
  id INT AUTO_INCREMENT PRIMARY KEY,
  requester_id INT NOT NULL,
  disaster_id INT NOT NULL,
  category VARCHAR(60) NOT NULL,
  description TEXT NOT NULL,
  people_count INT NOT NULL DEFAULT 1,
  urgency VARCHAR(30) NOT NULL DEFAULT 'high',
  contact_phone VARCHAR(30) NOT NULL,
  latitude DECIMAL(10, 7) NOT NULL,
  longitude DECIMAL(10, 7) NOT NULL,
  location_accuracy DECIMAL(10, 2),
  status VARCHAR(40) NOT NULL DEFAULT 'requested',
  assigned_unit VARCHAR(160),
  responder_notes TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_supply_requester FOREIGN KEY (requester_id) REFERENCES users(id),
  CONSTRAINT fk_supply_disaster FOREIGN KEY (disaster_id) REFERENCES disasters(id),
  INDEX idx_supply_status_urgency (status, urgency, created_at),
  INDEX idx_supply_location (latitude, longitude)
);

CREATE TABLE donation_campaigns (
  id INT AUTO_INCREMENT PRIMARY KEY,
  disaster_id INT,
  title VARCHAR(180) NOT NULL,
  description TEXT NOT NULL,
  goal_amount DECIMAL(14, 2) NOT NULL,
  currency VARCHAR(10) NOT NULL DEFAULT 'INR',
  status VARCHAR(30) NOT NULL DEFAULT 'active',
  organizer VARCHAR(160) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  ends_at TIMESTAMP NULL,
  CONSTRAINT fk_campaign_disaster FOREIGN KEY (disaster_id) REFERENCES disasters(id),
  INDEX idx_campaign_status (status)
);

CREATE TABLE donations (
  id INT AUTO_INCREMENT PRIMARY KEY,
  campaign_id INT NOT NULL,
  donor_id INT,
  donor_name VARCHAR(120) NOT NULL,
  donor_email VARCHAR(160) NOT NULL,
  amount DECIMAL(14, 2) NOT NULL,
  currency VARCHAR(10) NOT NULL DEFAULT 'INR',
  anonymous BOOLEAN NOT NULL DEFAULT FALSE,
  message VARCHAR(500),
  reference VARCHAR(80) NOT NULL UNIQUE,
  status VARCHAR(30) NOT NULL DEFAULT 'pledged',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_donation_campaign FOREIGN KEY (campaign_id) REFERENCES donation_campaigns(id),
  CONSTRAINT fk_donation_user FOREIGN KEY (donor_id) REFERENCES users(id),
  INDEX idx_donation_campaign_status (campaign_id, status)
);

CREATE TABLE location_pings (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  rescue_request_id INT,
  supply_request_id INT,
  latitude DECIMAL(10, 7) NOT NULL,
  longitude DECIMAL(10, 7) NOT NULL,
  accuracy_meters DECIMAL(10, 2),
  source VARCHAR(30) NOT NULL DEFAULT 'device',
  consent_granted BOOLEAN NOT NULL,
  recorded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_location_user FOREIGN KEY (user_id) REFERENCES users(id),
  CONSTRAINT fk_location_rescue FOREIGN KEY (rescue_request_id) REFERENCES rescue_requests(id),
  CONSTRAINT fk_location_supply FOREIGN KEY (supply_request_id) REFERENCES supply_requests(id),
  INDEX idx_location_user_time (user_id, recorded_at)
);

CREATE TABLE response_dispatches (
  id INT AUTO_INCREMENT PRIMARY KEY,
  rescue_request_id INT NOT NULL,
  responder_type VARCHAR(40) NOT NULL,
  responder_id INT NOT NULL,
  responder_name VARCHAR(160) NOT NULL,
  distance_km DECIMAL(10, 2) NOT NULL,
  status VARCHAR(30) NOT NULL DEFAULT 'assigned',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_response_dispatch_rescue FOREIGN KEY (rescue_request_id) REFERENCES rescue_requests(id),
  INDEX idx_response_dispatch_rescue (rescue_request_id, responder_type),
  INDEX idx_response_dispatch_status (status)
);

CREATE TABLE responder_units (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(160) NOT NULL UNIQUE,
  unit_type VARCHAR(50) NOT NULL,
  skills VARCHAR(255) NOT NULL,
  contact_phone VARCHAR(30) NOT NULL,
  latitude DECIMAL(10, 7) NOT NULL,
  longitude DECIMAL(10, 7) NOT NULL,
  availability_status VARCHAR(30) NOT NULL DEFAULT 'available',
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_responder_unit_type (unit_type),
  INDEX idx_responder_unit_availability (availability_status),
  INDEX idx_responder_unit_location (latitude, longitude)
);
