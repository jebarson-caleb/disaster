export function estimateDamage(report) {
  const disasterWeights = { flood: 22, earthquake: 30, cyclone: 26, landslide: 24, fire: 28 };
  const severityWeights = { low: 10, medium: 25, high: 45, critical: 65 };
  const score = clamp(
    15 +
      (disasterWeights[report.disaster_type] || 18) +
      (severityWeights[report.severity_hint] || 25) +
      Math.min(25, Math.floor(Number(report.people_affected || 0) / 20)) +
      (report.image_url ? 5 : 0),
  );
  return {
    score,
    label: labelFromScore(score),
    explanation: `${labelFromScore(score)} damage estimated from ${report.disaster_type}, ${report.people_affected || 0} people affected, and ${report.severity_hint} severity signal.`,
  };
}

export function prioritizeRescue(request, disasterType = 'flood') {
  let score = 20;
  const condition = String(request.condition || 'stable').toLowerCase();
  if (['critical', 'unconscious', 'bleeding', 'serious'].includes(condition)) score += 35;
  else if (['injured', 'sick'].includes(condition)) score += 20;
  if (request.trapped) score += 25;
  if (['flood', 'fire', 'earthquake', 'landslide'].includes(disasterType)) score += 10;
  score += Math.min(15, Number(request.vulnerable_people || 0) * 5);
  score += Math.min(10, Math.max(0, Number(request.people_count || 1) - 1) * 2);
  const age = Number(request.victim_age || 0);
  if (age && (age < 12 || age > 65)) score += 10;
  score = clamp(score);
  return {
    score,
    label: labelFromScore(score),
    explanation: `${labelFromScore(score)} priority because condition is ${condition}, trapped is ${request.trapped ? 'yes' : 'no'}, and vulnerable count is ${request.vulnerable_people || 0}.`,
  };
}

export function allocateResources(input) {
  const severity = String(input.severity || 'medium').toLowerCase();
  const people = Number(input.people_count || input.people_affected || 1);
  const isCritical = severity === 'critical';
  return {
    ambulances: isCritical ? 2 : severity === 'high' ? 1 : 0,
    rescue_teams: isCritical ? 3 : 1,
    volunteers: Math.max(2, Math.ceil(people / 20)),
    food_packets: Math.max(25, people * 3),
    medicine_kits: Math.max(5, Math.ceil(people / 8)),
    shelter_slots: ['flood', 'cyclone', 'fire'].includes(input.disaster_type) ? people : Math.ceil(people / 2),
  };
}

function labelFromScore(score) {
  if (score >= 85) return 'Critical';
  if (score >= 65) return 'High';
  if (score >= 40) return 'Medium';
  return 'Low';
}

function clamp(value) {
  return Math.max(0, Math.min(100, Math.round(value)));
}
