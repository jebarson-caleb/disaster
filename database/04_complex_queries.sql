USE disaster_response;

-- 1. Highest-priority pending rescues with disaster context.
SELECT r.id, r.victim_name, r.priority_score, r.priority_label, d.title, d.disaster_type, d.address
FROM rescue_requests r
JOIN disasters d ON d.id = r.disaster_id
WHERE r.status = 'pending'
ORDER BY r.priority_score DESC, r.created_at ASC
LIMIT 20;

-- 2. Hospital capacity near emergency load by disaster type.
SELECT d.disaster_type, COUNT(r.id) AS active_requests, SUM(h.available_beds) AS visible_beds
FROM disasters d
JOIN rescue_requests r ON r.disaster_id = d.id
CROSS JOIN hospitals h
WHERE d.status = 'active' AND r.status IN ('pending', 'assigned', 'en route')
GROUP BY d.disaster_type;

-- 3. Resource distribution totals per disaster.
SELECT d.title, res.category, SUM(rd.quantity) AS total_quantity
FROM resource_distribution rd
JOIN resources res ON res.id = rd.resource_id
JOIN disasters d ON d.id = rd.disaster_id
GROUP BY d.title, res.category
ORDER BY d.title, res.category;

-- 4. Shelters with enough capacity for large rescue groups.
SELECT s.name, s.available_capacity, r.id AS rescue_request_id, r.people_count
FROM shelters s
JOIN rescue_requests r ON s.available_capacity >= r.people_count
WHERE r.status IN ('pending','assigned')
ORDER BY r.priority_score DESC, s.available_capacity DESC;

-- 5. AI assessment history for current active disasters.
SELECT d.title, a.assessment_type, a.score, a.label, a.explanation, a.created_at
FROM ai_assessments a
JOIN disasters d ON d.id = a.entity_id AND a.entity_type = 'disaster'
WHERE d.status = 'active'
ORDER BY a.created_at DESC;
