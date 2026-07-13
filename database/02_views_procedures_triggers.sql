USE disaster_response;

CREATE OR REPLACE VIEW active_emergencies AS
SELECT d.id, d.title, d.disaster_type, d.address, d.people_affected, d.severity_hint,
       COUNT(r.id) AS rescue_requests,
       MAX(r.priority_score) AS max_priority
FROM disasters d
LEFT JOIN rescue_requests r ON r.disaster_id = d.id
WHERE d.status = 'active'
GROUP BY d.id;

CREATE OR REPLACE VIEW hospital_availability AS
SELECT id, name, address, available_beds, icu_beds, emergency_capacity
FROM hospitals
WHERE available_beds > 0 OR emergency_capacity > 0;

CREATE OR REPLACE VIEW shelter_availability AS
SELECT id, name, address, available_capacity, food_available, medical_support
FROM shelters
WHERE available_capacity > 0;

CREATE OR REPLACE VIEW pending_high_priority_rescues AS
SELECT r.*, d.title AS disaster_title, d.disaster_type
FROM rescue_requests r
JOIN disasters d ON d.id = r.disaster_id
WHERE r.status = 'pending' AND r.priority_score >= 65
ORDER BY r.priority_score DESC, r.created_at ASC;

DELIMITER //

CREATE PROCEDURE assign_rescue_unit(
  IN p_rescue_request_id INT,
  IN p_assigned_unit VARCHAR(120),
  IN p_changed_by_id INT
)
BEGIN
  UPDATE rescue_requests
  SET assigned_unit = p_assigned_unit, status = 'assigned'
  WHERE id = p_rescue_request_id;

  INSERT INTO rescue_status_history (rescue_request_id, status, note, changed_by_id)
  VALUES (p_rescue_request_id, 'assigned', CONCAT('Assigned to ', p_assigned_unit), p_changed_by_id);
END//

CREATE PROCEDURE plan_resource_distribution(
  IN p_resource_id INT,
  IN p_disaster_id INT,
  IN p_quantity INT,
  IN p_destination VARCHAR(180)
)
BEGIN
  INSERT INTO resource_distribution (resource_id, disaster_id, quantity, destination, status)
  VALUES (p_resource_id, p_disaster_id, p_quantity, p_destination, 'planned');

  UPDATE resources
  SET available_quantity = GREATEST(0, available_quantity - p_quantity)
  WHERE id = p_resource_id;
END//

CREATE TRIGGER rescue_request_created_history
AFTER INSERT ON rescue_requests
FOR EACH ROW
BEGIN
  INSERT INTO rescue_status_history (rescue_request_id, status, note, changed_by_id)
  VALUES (NEW.id, NEW.status, 'Request created', NEW.requester_id);
END//

CREATE TRIGGER hospital_capacity_audit
AFTER UPDATE ON hospitals
FOR EACH ROW
BEGIN
  IF OLD.available_beds <> NEW.available_beds
     OR OLD.icu_beds <> NEW.icu_beds
     OR OLD.emergency_capacity <> NEW.emergency_capacity THEN
    INSERT INTO hospital_capacity_logs (hospital_id, available_beds, icu_beds, emergency_capacity)
    VALUES (NEW.id, NEW.available_beds, NEW.icu_beds, NEW.emergency_capacity);
  END IF;
END//

CREATE TRIGGER shelter_capacity_audit
AFTER UPDATE ON shelters
FOR EACH ROW
BEGIN
  IF OLD.available_capacity <> NEW.available_capacity THEN
    INSERT INTO shelter_capacity_logs (shelter_id, available_capacity)
    VALUES (NEW.id, NEW.available_capacity);
  END IF;
END//

DELIMITER ;
