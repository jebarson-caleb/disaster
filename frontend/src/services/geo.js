const EARTH_RADIUS_KM = 6371;
// Conservative average road speed for an emergency vehicle in disaster-affected traffic.
const RESPONSE_SPEED_KMH = 30;

export function distanceKm(from, to) {
  const values = [from?.latitude, from?.longitude, to?.latitude, to?.longitude].map(Number);
  if (values.some((value) => !Number.isFinite(value))) return null;
  const [lat1, lon1, lat2, lon2] = values;
  const toRadians = (degrees) => (degrees * Math.PI) / 180;
  const dLat = toRadians(lat2 - lat1);
  const dLon = toRadians(lon2 - lon1);
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(toRadians(lat1)) * Math.cos(toRadians(lat2)) * Math.sin(dLon / 2) ** 2;
  return 2 * EARTH_RADIUS_KM * Math.asin(Math.sqrt(a));
}

export function estimatedTravelMinutes(from, to, speedKmh = RESPONSE_SPEED_KMH) {
  const distance = distanceKm(from, to);
  if (distance == null) return null;
  return Math.max(1, Math.round((distance / speedKmh) * 60));
}

export function nearestItem(origin, items) {
  let best = null;
  for (const item of items) {
    const distance = distanceKm(origin, item);
    if (distance != null && (best == null || distance < best.distance)) best = { item, distance };
  }
  return best;
}
