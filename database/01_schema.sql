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
