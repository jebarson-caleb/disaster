import React, { useEffect, useMemo, useState } from 'react';
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion';
import { Bar, Doughnut, Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  ArcElement,
  BarElement,
  CategoryScale,
  Filler,
  Legend,
  LineElement,
  LinearScale,
  PointElement,
  Tooltip,
} from 'chart.js';
import { MapContainer, CircleMarker, Popup, TileLayer } from 'react-leaflet';
import {
  Activity,
  AlertTriangle,
  Ambulance,
  ArrowUpDown,
  Bell,
  Building2,
  CalendarDays,
  ClipboardList,
  Crosshair,
  Database,
  Gauge,
  HeartPulse,
  Home,
  MapPin,
  Megaphone,
  MessageSquare,
  MoreVertical,
  Navigation,
  Package,
  Plus,
  RadioTower,
  Search,
  Send,
  ShieldAlert,
  Siren,
  SlidersHorizontal,
  TrendingUp,
  UserRound,
  Users,
  Wifi,
  Zap,
} from 'lucide-react';
import MetricTile from './components/MetricTile.jsx';
import StatusPill from './components/StatusPill.jsx';
import { allocateResources, estimateDamage, prioritizeRescue } from './services/ai.js';
import { initialDisasters, initialFacilities, initialRescues, roles } from './services/mockData.js';

ChartJS.register(ArcElement, BarElement, CategoryScale, Filler, Legend, LineElement, LinearScale, PointElement, Tooltip);

const disasterOptions = ['flood', 'earthquake', 'cyclone', 'landslide', 'fire'];
const severityOptions = ['low', 'medium', 'high', 'critical'];
const conditionOptions = ['stable', 'injured', 'critical', 'unconscious', 'bleeding'];
const dashboardTabs = [
  { id: 'overview', label: 'Overview', icon: Gauge },
  { id: 'response', label: 'Response', icon: Siren },
  { id: 'health', label: 'Health', icon: HeartPulse },
  { id: 'logistics', label: 'Logistics', icon: Package },
];
const softSpring = { type: 'spring', stiffness: 420, damping: 34, mass: 0.8 };
const quickFade = { duration: 0.18, ease: [0.22, 1, 0.36, 1] };

const earlyWarningPillars = [
  { name: 'Risk knowledge', score: 82, detail: 'Loss history, exposure and vulnerable groups mapped', icon: Database },
  { name: 'Monitoring', score: 76, detail: 'Weather, field reports and incident sensors tracked', icon: Wifi },
  { name: 'Communication', score: 88, detail: 'SMS, siren, radio and volunteer relay prepared', icon: Megaphone },
  { name: 'Preparedness', score: 71, detail: 'Shelter, hospital and resource readiness reviewed', icon: ClipboardList },
];

const resourceInventory = [
  { name: 'Rescue boats', available: 12, total: 16, unit: 'boats', tone: 'blue' },
  { name: 'Food packets', available: 2500, total: 4200, unit: 'packs', tone: 'green' },
  { name: 'Medicine kits', available: 800, total: 1200, unit: 'kits', tone: 'orange' },
  { name: 'Water cans', available: 1600, total: 2400, unit: 'cans', tone: 'cyan' },
];

const fieldTeams = [
  { name: 'Boat Rescue Unit 2', status: 'assigned', eta: '12 min', location: 'Riverside Colony', load: 84 },
  { name: 'Fire Rescue Team 4', status: 'mobilizing', eta: '18 min', location: 'Market Road', load: 62 },
  { name: 'Volunteer Team A', status: 'en route', eta: '9 min', location: 'North Pier', load: 57 },
  { name: 'Medical Triage Van', status: 'available', eta: 'ready', location: 'City Emergency Hospital', load: 31 },
];

const standardsFeatures = [
  { label: 'CAP alert templates', detail: 'All-hazard public warnings across SMS, siren, radio and web.', icon: Megaphone },
  { label: 'Incident command roles', detail: 'Clear ownership for command, operations, logistics and medical.', icon: RadioTower },
  { label: 'Typed resource inventory', detail: 'Track boats, ambulances, kits, shelters and trained people.', icon: Package },
  { label: 'Mutual-aid requests', detail: 'Escalate shortages to partner NGOs and nearby agencies.', icon: Users },
  { label: 'Situation reports', detail: 'Share verified updates, constraints and next operational needs.', icon: ClipboardList },
];

const responseTrend = [
  { time: '08:00', reports: 4, rescued: 1 },
  { time: '09:00', reports: 9, rescued: 3 },
  { time: '10:00', reports: 14, rescued: 6 },
  { time: '11:00', reports: 18, rescued: 10 },
  { time: '12:00', reports: 24, rescued: 13 },
  { time: '13:00', reports: 27, rescued: 17 },
];

const initialAlerts = [
  { id: 1, audience: 'Ward 14 - Riverside', channel: 'SMS + radio', message: 'Move to Govt HSS Relief Camp. Avoid low-lying road near canal.', time: '8 min ago' },
  { id: 2, audience: 'Hospital network', channel: 'Ops dashboard', message: 'Prepare 25 emergency beds for flood response corridor.', time: '24 min ago' },
];

const roleNavigation = {
  Admin: [
    { id: 'command', label: 'Command', icon: RadioTower },
    { id: 'report', label: 'Report Disaster', icon: MapPin },
    { id: 'rescue', label: 'Rescue Queue', icon: HeartPulse },
    { id: 'facilities', label: 'Facilities', icon: Building2 },
  ],
  Citizen: [
    { id: 'command', label: 'My Safety', icon: Home },
    { id: 'report', label: 'Report Help', icon: MapPin },
    { id: 'rescue', label: 'Track Request', icon: HeartPulse },
  ],
  Hospital: [
    { id: 'command', label: 'Hospital Ops', icon: HeartPulse },
    { id: 'facilities', label: 'Capacity', icon: Building2 },
    { id: 'rescue', label: 'Incoming Triage', icon: Siren },
  ],
  Shelter: [
    { id: 'command', label: 'Shelter Ops', icon: Home },
    { id: 'facilities', label: 'Capacity', icon: Building2 },
  ],
  Ambulance: [
    { id: 'command', label: 'Dispatch', icon: Ambulance },
    { id: 'rescue', label: 'Assigned Calls', icon: Navigation },
    { id: 'facilities', label: 'Hospitals', icon: Building2 },
  ],
  NGO: [
    { id: 'command', label: 'Relief Ops', icon: Package },
    { id: 'rescue', label: 'Needs Queue', icon: ClipboardList },
    { id: 'facilities', label: 'Shelters', icon: Home },
    { id: 'report', label: 'Field Report', icon: MapPin },
  ],
  Volunteer: [
    { id: 'command', label: 'My Assignment', icon: Users },
    { id: 'rescue', label: 'Tasks', icon: ClipboardList },
  ],
  Police: [
    { id: 'command', label: 'Public Safety', icon: ShieldAlert },
    { id: 'rescue', label: 'Queue', icon: HeartPulse },
    { id: 'report', label: 'Incident Report', icon: MapPin },
  ],
  'Fire Service': [
    { id: 'command', label: 'Fire Rescue', icon: Siren },
    { id: 'rescue', label: 'Rescue Queue', icon: HeartPulse },
    { id: 'report', label: 'Field Report', icon: MapPin },
  ],
};

const roleTopbar = {
  Admin: { eyebrow: 'Operational dashboard', title: 'Emergency coordination center', action: 'Review priority queue', view: 'rescue', icon: ShieldAlert },
  Citizen: { eyebrow: 'Citizen portal', title: 'Report, track and stay safe', action: 'Report emergency', view: 'report', icon: MapPin },
  Hospital: { eyebrow: 'Hospital command', title: 'Capacity, triage and patient flow', action: 'Update capacity', view: 'facilities', icon: HeartPulse },
  Shelter: { eyebrow: 'Shelter command', title: 'Occupancy, intake and relief supplies', action: 'Update shelter capacity', view: 'facilities', icon: Home },
  Ambulance: { eyebrow: 'Ambulance dispatch', title: 'Assigned calls, ETA and hospital handoff', action: 'Open assigned calls', view: 'rescue', icon: Ambulance },
  NGO: { eyebrow: 'Relief coordination', title: 'Distribution, volunteers and unmet needs', action: 'Review needs queue', view: 'rescue', icon: Package },
  Volunteer: { eyebrow: 'Volunteer workspace', title: 'Assignments, safety and check-in', action: 'Open tasks', view: 'rescue', icon: Users },
  Police: { eyebrow: 'Public safety operations', title: 'Perimeters, road access and crowd safety', action: 'Review incidents', view: 'rescue', icon: ShieldAlert },
  'Fire Service': { eyebrow: 'Fire and rescue operations', title: 'Rescue hazards, teams and equipment', action: 'Open rescue queue', view: 'rescue', icon: Siren },
};

const assignCapableRoles = new Set(['Admin', 'Police', 'Fire Service', 'Ambulance', 'NGO']);

export default function App() {
  const reduceMotion = useReducedMotion();
  const [activeRole, setActiveRole] = useState('Citizen');
  const [activeView, setActiveView] = useState('command');
  const [dashboardMode, setDashboardMode] = useState('overview');
  const [disasters, setDisasters] = useState(initialDisasters);
  const [rescues, setRescues] = useState(initialRescues);
  const [facilities, setFacilities] = useState(initialFacilities);
  const [alerts, setAlerts] = useState(initialAlerts);
  const [alertDraft, setAlertDraft] = useState({
    audience: 'Coastal wards',
    channel: 'SMS + siren + volunteer relay',
    message: 'Heavy rainfall expected. Move vulnerable residents to the nearest open shelter.',
  });
  const [incidentDraft, setIncidentDraft] = useState({
    title: '',
    disaster_type: 'flood',
    address: '',
    description: '',
    latitude: 9.9312,
    longitude: 76.2673,
    people_affected: 25,
    severity_hint: 'medium',
  });
  const [rescueDraft, setRescueDraft] = useState({
    disaster_id: 1,
    victim_name: '',
    victim_age: 30,
    people_count: 1,
    condition: 'injured',
    trapped: false,
    vulnerable_people: 0,
    latitude: 9.932,
    longitude: 76.269,
    notes: '',
  });

  const metrics = useMemo(() => {
    const pending = rescues.filter((item) => item.status === 'pending').length;
    const assigned = rescues.filter((item) => item.status === 'assigned' || item.status === 'en route').length;
    const critical = rescues.filter((item) => item.priority_label === 'Critical').length;
    const beds = facilities.hospitals.reduce((sum, item) => sum + item.available_beds, 0);
    const totalBeds = facilities.hospitals.reduce((sum, item) => sum + item.total_beds, 0);
    const shelterCapacity = facilities.shelters.reduce((sum, item) => sum + item.available_capacity, 0);
    const totalShelterCapacity = facilities.shelters.reduce((sum, item) => sum + item.total_capacity, 0);
    const availableAmbulances = facilities.ambulances.filter((item) => item.status === 'available').length;
    const affectedPeople = disasters.reduce((sum, item) => sum + Number(item.people_affected || 0), 0);
    const avgPriority = Math.round(rescues.reduce((sum, item) => sum + item.priority_score, 0) / Math.max(1, rescues.length));
    const readinessScore = Math.round(earlyWarningPillars.reduce((sum, item) => sum + item.score, 0) / earlyWarningPillars.length);
    return {
      pending,
      assigned,
      critical,
      beds,
      totalBeds,
      shelterCapacity,
      totalShelterCapacity,
      availableAmbulances,
      affectedPeople,
      avgPriority,
      readinessScore,
    };
  }, [rescues, facilities, disasters]);

  const priorityChart = useMemo(() => {
    const labels = ['Critical', 'High', 'Medium', 'Low'];
    const counts = labels.map((label) => rescues.filter((item) => item.priority_label === label).length);
    return {
      labels,
      datasets: [{ data: counts, backgroundColor: ['#dc2626', '#f97316', '#0891b2', '#2563eb'], borderWidth: 0 }],
    };
  }, [rescues]);

  const disasterChart = useMemo(() => {
    const labels = disasterOptions;
    const counts = labels.map((type) => disasters.filter((item) => item.disaster_type === type).length);
    return {
      labels,
      datasets: [{ label: 'Active reports', data: counts, backgroundColor: '#0f766e', borderRadius: 6, maxBarThickness: 34 }],
    };
  }, [disasters]);

  const trendChart = useMemo(
    () => ({
      labels: responseTrend.map((item) => item.time),
      datasets: [
        {
          label: 'Incoming reports',
          data: responseTrend.map((item) => item.reports),
          borderColor: '#dc2626',
          backgroundColor: 'rgba(220, 38, 38, 0.12)',
          fill: true,
          tension: 0.35,
          pointRadius: 3,
        },
        {
          label: 'Rescues completed',
          data: responseTrend.map((item) => item.rescued),
          borderColor: '#0f766e',
          backgroundColor: 'rgba(15, 118, 110, 0.1)',
          fill: true,
          tension: 0.35,
          pointRadius: 3,
        },
      ],
    }),
    [],
  );

  const sortedRescues = [...rescues].sort((a, b) => b.priority_score - a.priority_score);
  const selectedDisaster = disasters.find((item) => Number(item.id) === Number(rescueDraft.disaster_id)) || disasters[0];
  const allocation = allocateResources({
    severity: sortedRescues[0]?.priority_label || 'Medium',
    people_count: selectedDisaster?.people_affected || 1,
    disaster_type: selectedDisaster?.disaster_type || 'flood',
  });
  const activeTopbar = roleTopbar[activeRole] || roleTopbar.Admin;
  const activeNavigation = roleNavigation[activeRole] || roleNavigation.Admin;
  const PrimaryIcon = activeTopbar.icon;
  const visibleRescues = rescueItemsForRole(activeRole, sortedRescues);

  useEffect(() => {
    if (!activeNavigation.some((item) => item.id === activeView)) {
      setActiveView('command');
    }
  }, [activeRole, activeNavigation, activeView]);

  function submitIncident(event) {
    event.preventDefault();
    const assessment = estimateDamage(incidentDraft);
    const next = {
      id: Date.now(),
      ...incidentDraft,
      latitude: Number(incidentDraft.latitude),
      longitude: Number(incidentDraft.longitude),
      people_affected: Number(incidentDraft.people_affected),
      status: 'active',
      score: assessment.score,
      label: assessment.label,
      created_at: 'Just now',
    };
    setDisasters([next, ...disasters]);
    setIncidentDraft({ ...incidentDraft, title: '', address: '', description: '', people_affected: 25 });
    setActiveView('command');
  }

  function submitRescue(event) {
    event.preventDefault();
    const disaster = disasters.find((item) => Number(item.id) === Number(rescueDraft.disaster_id));
    const priority = prioritizeRescue(rescueDraft, disaster?.disaster_type);
    const next = {
      id: Date.now(),
      ...rescueDraft,
      latitude: Number(rescueDraft.latitude),
      longitude: Number(rescueDraft.longitude),
      victim_age: Number(rescueDraft.victim_age),
      people_count: Number(rescueDraft.people_count),
      vulnerable_people: Number(rescueDraft.vulnerable_people),
      status: 'pending',
      priority_score: priority.score,
      priority_label: priority.label,
      assigned_unit: '',
      created_at: 'Just now',
    };
    setRescues([next, ...rescues]);
    setRescueDraft({ ...rescueDraft, victim_name: '', notes: '', trapped: false });
    setActiveView('rescue');
  }

  function sendAlert(event) {
    event.preventDefault();
    const next = { id: Date.now(), ...alertDraft, time: 'Just now' };
    setAlerts([next, ...alerts]);
    setAlertDraft({ ...alertDraft, message: '' });
  }

  function assignRescue(id) {
    setRescues((items) =>
      items.map((item) =>
        item.id === id
          ? {
              ...item,
              status: 'assigned',
              assigned_unit: item.priority_label === 'Critical' ? 'Rapid Rescue Unit' : 'Volunteer Team',
            }
          : item,
      ),
    );
  }

  function updateHospital(id, delta) {
    setFacilities((current) => ({
      ...current,
      hospitals: current.hospitals.map((item) =>
        item.id === id ? { ...item, available_beds: Math.max(0, item.available_beds + delta) } : item,
      ),
    }));
  }

  function updateShelter(id, delta) {
    setFacilities((current) => ({
      ...current,
      shelters: current.shelters.map((item) =>
        item.id === id ? { ...item, available_capacity: Math.max(0, item.available_capacity + delta) } : item,
      ),
    }));
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <div className="brand-mark">
            <ShieldAlert size={24} />
          </div>
          <div>
            <strong>ResQ Command</strong>
            <span>Disaster response platform</span>
          </div>
        </div>

        <label className="field-label" htmlFor="role-select">
          Active role
        </label>
        <select id="role-select" className="form-select" value={activeRole} onChange={(event) => setActiveRole(event.target.value)}>
          {roles.map((role) => (
            <option key={role}>{role}</option>
          ))}
        </select>

        <nav className="nav-stack" aria-label="Main views">
          {activeNavigation.map(({ id, label, icon: Icon }) => (
            <button key={id} className={activeView === id ? 'active' : ''} onClick={() => setActiveView(id)}>
              <Icon size={18} /> {label}
            </button>
          ))}
        </nav>

        <div className="side-score">
          <span>Early warning readiness</span>
          <strong>{metrics.readinessScore}%</strong>
          <ProgressBar value={metrics.readinessScore} />
        </div>

        <div className="role-note">
          <Bell size={16} />
          <span>{roleMessage(activeRole)}</span>
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div className="search-shell">
            <Search size={18} />
            <input aria-label="Search operations" placeholder="Search incident, shelter, patient..." />
          </div>
          <div className="topbar-tools">
            <button type="button">
              <ArrowUpDown size={16} />
              Sort by
            </button>
            <button type="button">
              <SlidersHorizontal size={16} />
              Filters
            </button>
            <button type="button">
              <UserRound size={16} />
              {activeRole}
            </button>
            <button className="primary-action" onClick={() => setActiveView(activeTopbar.view)}>
              <Plus size={17} />
              {activeTopbar.action}
            </button>
          </div>
        </header>

        <section className="page-heading">
          <div>
            <p>{activeTopbar.eyebrow}</p>
            <h1>{activeTopbar.title}</h1>
          </div>
          <StatusPill value={activeRole} />
        </section>

        <AnimatePresence mode="wait">
          {activeView === 'command' && (
            <MotionPage key="command" reduceMotion={reduceMotion}>
              {activeRole === 'Admin' ? (
                <CommandView
                  metrics={metrics}
                  disasters={disasters}
                  rescues={sortedRescues}
                  priorityChart={priorityChart}
                  disasterChart={disasterChart}
                  trendChart={trendChart}
                  allocation={allocation}
                  dashboardMode={dashboardMode}
                  setDashboardMode={setDashboardMode}
                  alerts={alerts}
                  alertDraft={alertDraft}
                  setAlertDraft={setAlertDraft}
                  sendAlert={sendAlert}
                  reduceMotion={reduceMotion}
                />
              ) : (
                <RoleDashboard
                  role={activeRole}
                  metrics={metrics}
                  disasters={disasters}
                  rescues={visibleRescues}
                  facilities={facilities}
                  alerts={alerts}
                  setActiveView={setActiveView}
                />
              )}
            </MotionPage>
          )}
          {activeView === 'report' && (
            <MotionPage key="report" reduceMotion={reduceMotion}>
              <ReportView
                draft={incidentDraft}
                setDraft={setIncidentDraft}
                onSubmit={submitIncident}
                rescueDraft={rescueDraft}
                setRescueDraft={setRescueDraft}
                disasters={disasters}
                onRescueSubmit={submitRescue}
              />
            </MotionPage>
          )}
          {activeView === 'rescue' && (
            <MotionPage key="rescue" reduceMotion={reduceMotion}>
              <RescueView role={activeRole} rescues={visibleRescues} disasters={disasters} onAssign={assignRescue} />
            </MotionPage>
          )}
          {activeView === 'facilities' && (
            <MotionPage key="facilities" reduceMotion={reduceMotion}>
              <FacilitiesView role={activeRole} facilities={facilities} updateHospital={updateHospital} updateShelter={updateShelter} />
            </MotionPage>
          )}
        </AnimatePresence>
      </section>
    </main>
  );
}

function MotionPage({ children, reduceMotion }) {
  return <div className="motion-page">{children}</div>;
}

function RoleDashboard({ role, metrics, disasters, rescues, facilities, alerts, setActiveView }) {
  const workspace = getRoleWorkspace(role, { metrics, disasters, rescues, facilities, alerts });
  const HeroIcon = workspace.icon;

  return (
    <div className="view-stack">
      <section className="role-hero">
        <div className="role-hero-main">
          <div className="role-hero-icon">
            <HeroIcon size={24} />
          </div>
          <div>
            <p className="eyebrow">{workspace.eyebrow}</p>
            <h2>{workspace.title}</h2>
            <span>{workspace.summary}</span>
          </div>
        </div>
        <div className="role-action-strip">
          {workspace.actions.map((action) => {
            const Icon = action.icon;
            return (
              <button key={action.label} onClick={() => setActiveView(action.view)}>
                <Icon size={16} />
                {action.label}
              </button>
            );
          })}
        </div>
      </section>

      <section className="role-metrics-grid">
        {workspace.metrics.map((item) => (
          <div className="role-metric" key={item.label}>
            <span>{item.label}</span>
            <strong>{item.value}</strong>
            <p>{item.detail}</p>
          </div>
        ))}
      </section>

      <section className="role-content-grid">
        <section className="panel">
          <PanelTitle eyebrow={workspace.focus.eyebrow} title={workspace.focus.title} />
          <div className="role-task-list">
            {workspace.tasks.map((task) => (
              <div className="role-task" key={task.title}>
                <StatusPill value={task.status} />
                <div>
                  <strong>{task.title}</strong>
                  <span>{task.detail}</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="panel">
          <PanelTitle eyebrow={workspace.second.eyebrow} title={workspace.second.title} />
          <div className="role-signal-list">
            {workspace.signals.map((signal) => {
              const Icon = signal.icon;
              return (
                <div className="role-signal" key={signal.label}>
                  <Icon size={18} />
                  <div>
                    <strong>{signal.label}</strong>
                    <span>{signal.detail}</span>
                  </div>
                  <strong>{signal.value}</strong>
                </div>
              );
            })}
          </div>
        </section>

        <section className="panel role-guidance-panel">
          <PanelTitle eyebrow="Recommended features" title="Role-specific tools" />
          <div className="role-guidance-list">
            {workspace.features.map((feature) => (
              <div key={feature}>
                <ClipboardList size={16} />
                <span>{feature}</span>
              </div>
            ))}
          </div>
        </section>
      </section>
    </div>
  );
}

function getRoleWorkspace(role, { metrics, disasters, rescues, facilities, alerts }) {
  const topRescue = rescues[0];
  const activeDisaster = disasters[0];
  const firstHospital = facilities.hospitals[0];
  const firstShelter = facilities.shelters[0];
  const firstAmbulance = facilities.ambulances[0];
  const base = {
    Citizen: {
      icon: Home,
      eyebrow: 'Citizen safety workspace',
      title: 'Get help, follow warnings and reach safe shelter',
      summary: 'Focused on emergency reporting, rescue tracking, official alerts and nearby capacity.',
      metrics: [
        { label: 'Nearest shelter slots', value: metrics.shelterCapacity, detail: `${firstShelter?.name || 'Relief camp'} currently receiving people` },
        { label: 'Hospital beds visible', value: metrics.beds, detail: 'For emergency referral and ambulance handoff' },
        { label: 'Active warnings', value: alerts.length, detail: 'Official messages in your area' },
        { label: 'My request status', value: topRescue?.status || 'None', detail: topRescue?.assigned_unit || 'No active dispatch assigned' },
      ],
      focus: { eyebrow: 'Safety plan', title: 'Immediate citizen actions' },
      second: { eyebrow: 'Nearby support', title: 'Where to go next' },
      tasks: [
        { title: 'Report urgent help with exact location', detail: 'Use the report form before phone battery or network drops.', status: 'High' },
        { title: 'Move vulnerable people first', detail: 'Children, elderly and injured people should move to open shelter.', status: 'Active' },
        { title: 'Follow official alert channel', detail: alerts[0]?.message || 'Await updated warning from command.', status: 'Live' },
      ],
      signals: [
        { label: 'Open shelter', value: firstShelter?.available_capacity || 0, detail: firstShelter?.name || 'Shelter capacity', icon: Home },
        { label: 'Medical support', value: firstShelter?.medical_support ? 'Yes' : 'Basic', detail: 'Shelter medical assistance status', icon: HeartPulse },
        { label: 'Emergency route', value: 'Open', detail: activeDisaster?.address || 'Nearest safe route', icon: Navigation },
      ],
      actions: [
        { label: 'Report emergency', view: 'report', icon: MapPin },
        { label: 'Track request', view: 'rescue', icon: HeartPulse },
      ],
      features: ['Personal rescue timeline', 'Nearest shelter and hospital visibility', 'Preparedness checklist and alert feed'],
    },
    Hospital: {
      icon: HeartPulse,
      eyebrow: 'Hospital emergency workspace',
      title: 'Manage surge capacity and incoming triage',
      summary: 'Built for bed visibility, overflow planning, transfer readiness and emergency patient routing.',
      metrics: [
        { label: 'Available beds', value: metrics.beds, detail: `${metrics.totalBeds} total beds tracked` },
        { label: 'ICU beds', value: facilities.hospitals.reduce((sum, item) => sum + item.icu_beds, 0), detail: 'Critical care capacity' },
        { label: 'Incoming critical', value: metrics.critical, detail: 'AI-ranked rescue requests' },
        { label: 'Ambulances ready', value: metrics.availableAmbulances, detail: 'For transfer and pickup' },
      ],
      focus: { eyebrow: 'Triage operations', title: 'Hospital action board' },
      second: { eyebrow: 'Capacity signals', title: 'Surge readiness' },
      tasks: [
        { title: 'Activate triage desk', detail: 'Tag critical, delayed and walking wounded arrivals.', status: 'Active' },
        { title: 'Prepare overflow care area', detail: 'Use auditorium/lobby plan if emergency demand rises.', status: 'High' },
        { title: 'Coordinate patient transfer', detail: 'Share capacity with ambulance and command users.', status: 'Live' },
      ],
      signals: [
        { label: firstHospital?.name || 'Hospital', value: firstHospital?.available_beds || 0, detail: 'Available beds', icon: Building2 },
        { label: 'Emergency capacity', value: firstHospital?.emergency_capacity || 0, detail: 'Immediate intake capacity', icon: Siren },
        { label: 'Referral route', value: 'Ready', detail: 'Interfacility transfer plan', icon: Navigation },
      ],
      actions: [
        { label: 'Update capacity', view: 'facilities', icon: Building2 },
        { label: 'Incoming triage', view: 'rescue', icon: Siren },
      ],
      features: ['Bed/ICU/surge capacity board', 'Ambulance arrival handoff', 'Overflow and transfer checklist'],
    },
    Shelter: {
      icon: Home,
      eyebrow: 'Shelter operations workspace',
      title: 'Track occupancy, intake and relief support',
      summary: 'Focused on available slots, food/medical support, arrivals and unmet shelter needs.',
      metrics: [
        { label: 'Available slots', value: metrics.shelterCapacity, detail: `${metrics.totalShelterCapacity} total capacity` },
        { label: 'Food support', value: firstShelter?.food_available ? 'Ready' : 'Low', detail: 'Camp meal distribution status' },
        { label: 'Medical support', value: firstShelter?.medical_support ? 'On site' : 'Referral', detail: 'Basic triage capability' },
        { label: 'Expected arrivals', value: metrics.pending + metrics.assigned, detail: 'From active rescue queue' },
      ],
      focus: { eyebrow: 'Relief camp intake', title: 'Shelter action board' },
      second: { eyebrow: 'Camp signals', title: 'Capacity and supplies' },
      tasks: [
        { title: 'Update available capacity', detail: 'Keep command and citizens aware of free slots.', status: 'Live' },
        { title: 'Prepare family intake desk', detail: 'Record vulnerable people and medical needs.', status: 'Active' },
        { title: 'Flag supply shortage early', detail: 'Request food, water, blankets or medicines before stockout.', status: 'Medium' },
      ],
      signals: [
        { label: firstShelter?.name || 'Relief shelter', value: firstShelter?.available_capacity || 0, detail: 'Slots available', icon: Home },
        { label: 'Food', value: firstShelter?.food_available ? 'Ready' : 'Low', detail: 'Meal support status', icon: Package },
        { label: 'Medical', value: firstShelter?.medical_support ? 'Ready' : 'Referral', detail: 'Health desk availability', icon: HeartPulse },
      ],
      actions: [
        { label: 'Update capacity', view: 'facilities', icon: Home },
        { label: 'View arrivals', view: 'rescue', icon: Users },
      ],
      features: ['Occupancy and intake counter', 'Food/medicine shortage flags', 'Family reunification and vulnerable-person list'],
    },
    Ambulance: {
      icon: Ambulance,
      eyebrow: 'Ambulance dispatch workspace',
      title: 'Prioritize calls, ETA and hospital handoff',
      summary: 'Focused on assigned rescue calls, route visibility, patient condition and receiving capacity.',
      metrics: [
        { label: 'Assigned calls', value: metrics.assigned, detail: 'Active dispatches and en-route cases' },
        { label: 'Top priority', value: topRescue?.priority_label || 'None', detail: topRescue?.victim_name || 'No active call' },
        { label: 'Receiving beds', value: metrics.beds, detail: 'Hospital capacity available' },
        { label: 'Unit status', value: firstAmbulance?.status || 'Available', detail: firstAmbulance?.vehicle_number || 'Vehicle readiness' },
      ],
      focus: { eyebrow: 'Dispatch queue', title: 'Ambulance action board' },
      second: { eyebrow: 'Handoff signals', title: 'Route and hospital context' },
      tasks: [
        { title: 'Accept highest-priority dispatch', detail: topRescue?.notes || 'No high-priority dispatch waiting.', status: topRescue?.priority_label || 'Ready' },
        { title: 'Confirm receiving hospital', detail: `${firstHospital?.name || 'Hospital'} has ${firstHospital?.available_beds || metrics.beds} beds visible.`, status: 'Live' },
        { title: 'Update vehicle status', detail: 'Keep availability accurate for command allocation.', status: 'Active' },
      ],
      signals: [
        { label: 'ETA target', value: '12 min', detail: topRescue?.victim_name || 'Nearest call', icon: Navigation },
        { label: 'Patient condition', value: topRescue?.condition || 'stable', detail: 'Reported rescue condition', icon: HeartPulse },
        { label: 'Hospital handoff', value: firstHospital?.available_beds || metrics.beds, detail: 'Open beds', icon: Building2 },
      ],
      actions: [
        { label: 'Assigned calls', view: 'rescue', icon: Ambulance },
        { label: 'Hospital capacity', view: 'facilities', icon: Building2 },
      ],
      features: ['ETA and route card', 'Receiving hospital capacity', 'Vehicle availability update'],
    },
    NGO: {
      icon: Package,
      eyebrow: 'NGO relief workspace',
      title: 'Coordinate supplies, volunteers and unmet needs',
      summary: 'Built for local relief distribution, volunteer teams, shelter gaps and field assessment reports.',
      metrics: [
        { label: 'Food packets', value: '2,500', detail: 'Ready for distribution' },
        { label: 'Medicine kits', value: '800', detail: 'Warehouse stock' },
        { label: 'Open shelters', value: facilities.shelters.length, detail: `${metrics.shelterCapacity} free slots` },
        { label: 'Unmet needs', value: metrics.pending, detail: 'Pending high-priority requests' },
      ],
      focus: { eyebrow: 'Relief distribution', title: 'NGO action board' },
      second: { eyebrow: 'Coordination signals', title: 'Where support is needed' },
      tasks: [
        { title: 'Dispatch food and water to open shelters', detail: 'Prioritize high-occupancy camps and flood zones.', status: 'High' },
        { title: 'Assign volunteers to intake and logistics', detail: 'Match skills to shelter, WASH and relief tasks.', status: 'Active' },
        { title: 'Submit field assessment', detail: 'Report unmet household needs from the affected ward.', status: 'Live' },
      ],
      signals: [
        { label: 'Relief stock', value: 'Good', detail: 'Food, ORS and water cans available', icon: Package },
        { label: 'Volunteer teams', value: fieldTeams.length, detail: 'Teams visible in field operations', icon: Users },
        { label: 'Shelter gap', value: metrics.shelterCapacity, detail: 'Available relief slots', icon: Home },
      ],
      actions: [
        { label: 'Needs queue', view: 'rescue', icon: ClipboardList },
        { label: 'Field report', view: 'report', icon: MapPin },
      ],
      features: ['Distribution planning', 'Volunteer assignment by skill', 'Unmet-needs and shelter-gap board'],
    },
    Volunteer: {
      icon: Users,
      eyebrow: 'Volunteer workspace',
      title: 'Know your task, stay safe and check in',
      summary: 'Focused on assigned work, safety briefing, check-in status and nearby relief locations.',
      metrics: [
        { label: 'Assigned task', value: '1', detail: 'Volunteer Team A relocation support' },
        { label: 'Safety briefing', value: 'Due', detail: 'Floodwater and PPE reminder' },
        { label: 'Nearest shelter', value: firstShelter?.available_capacity || 0, detail: firstShelter?.name || 'Open shelter' },
        { label: 'Check-in', value: 'Ready', detail: 'No overdue check-in' },
      ],
      focus: { eyebrow: 'Assignment board', title: 'Volunteer action board' },
      second: { eyebrow: 'Safety signals', title: 'Before deployment' },
      tasks: [
        { title: 'Confirm availability', detail: 'Check in before moving to the assigned area.', status: 'Ready' },
        { title: 'Support shelter intake', detail: 'Help families register and identify vulnerable people.', status: 'Assigned' },
        { title: 'Report unsafe conditions', detail: 'Escalate blocked roads, live wires or contaminated water.', status: 'Live' },
      ],
      signals: [
        { label: 'PPE status', value: 'Packed', detail: 'Gloves, mask, torch, water', icon: ClipboardList },
        { label: 'Task area', value: 'North Pier', detail: 'Volunteer Team A route', icon: Navigation },
        { label: 'Buddy system', value: 'Required', detail: 'Do not deploy alone', icon: Users },
      ],
      actions: [
        { label: 'Open tasks', view: 'rescue', icon: ClipboardList },
        { label: 'Report hazard', view: 'report', icon: AlertTriangle },
      ],
      features: ['Check-in and safety briefing', 'Skill-matched task list', 'Hazard reporting from field'],
    },
    Police: {
      icon: ShieldAlert,
      eyebrow: 'Police public-safety workspace',
      title: 'Secure access, perimeters and rescue corridors',
      summary: 'Focused on road access, crowd control, evacuation zones and responder safety.',
      metrics: [
        { label: 'Active incidents', value: disasters.length, detail: 'Public-safety areas to monitor' },
        { label: 'Pending rescues', value: metrics.pending, detail: 'Require coordination support' },
        { label: 'Road corridors', value: '3 open', detail: 'Access routes for ambulances and rescue' },
        { label: 'Alerts sent', value: alerts.length, detail: 'Public warnings visible' },
      ],
      focus: { eyebrow: 'Public-safety board', title: 'Police action board' },
      second: { eyebrow: 'Access signals', title: 'Perimeters and movement' },
      tasks: [
        { title: 'Secure rescue corridor', detail: 'Keep route open for ambulance and fire rescue access.', status: 'High' },
        { title: 'Manage evacuation perimeter', detail: 'Guide citizens away from unstable or flooded areas.', status: 'Active' },
        { title: 'Verify public warning reach', detail: 'Confirm ward-level warnings are understood and actionable.', status: 'Live' },
      ],
      signals: [
        { label: 'Primary corridor', value: 'Open', detail: activeDisaster?.address || 'Incident access route', icon: Navigation },
        { label: 'Crowd control', value: 'Active', detail: 'Shelter intake and road junctions', icon: Users },
        { label: 'Hazards', value: metrics.critical, detail: 'Critical rescue zones', icon: AlertTriangle },
      ],
      actions: [
        { label: 'Review queue', view: 'rescue', icon: HeartPulse },
        { label: 'Incident report', view: 'report', icon: MapPin },
      ],
      features: ['Road closure and access corridor board', 'Evacuation perimeter tracking', 'Public warning acknowledgement'],
    },
    'Fire Service': {
      icon: Siren,
      eyebrow: 'Fire and rescue workspace',
      title: 'Track rescue hazards, teams and equipment',
      summary: 'Focused on fire/rescue incidents, trapped victims, equipment readiness and field-team safety.',
      metrics: [
        { label: 'Critical rescues', value: metrics.critical, detail: 'AI-prioritized trapped/injured cases' },
        { label: 'Fire incidents', value: disasters.filter((item) => item.disaster_type === 'fire').length, detail: 'Active fire reports' },
        { label: 'Rescue teams', value: fieldTeams.length, detail: 'Visible response teams' },
        { label: 'Equipment ready', value: '86%', detail: 'Boats, PPE and rescue gear' },
      ],
      focus: { eyebrow: 'Fire rescue board', title: 'Rescue action board' },
      second: { eyebrow: 'Hazard signals', title: 'Scene safety and equipment' },
      tasks: [
        { title: 'Prioritize trapped victims', detail: topRescue?.notes || 'No trapped victim in queue.', status: topRescue?.priority_label || 'Ready' },
        { title: 'Stage rescue equipment', detail: 'Check PPE, boat, rope and extrication gear readiness.', status: 'Active' },
        { title: 'Update scene status', detail: 'Share hazard, smoke, floodwater and structural risk changes.', status: 'Live' },
      ],
      signals: [
        { label: 'Scene hazard', value: topRescue?.priority_label || 'Medium', detail: activeDisaster?.title || 'Active incident', icon: AlertTriangle },
        { label: 'Team ETA', value: '18 min', detail: 'Fire Rescue Team 4 mobilizing', icon: Navigation },
        { label: 'Equipment', value: 'Ready', detail: 'Rescue kit and PPE staged', icon: Package },
      ],
      actions: [
        { label: 'Open queue', view: 'rescue', icon: HeartPulse },
        { label: 'Field report', view: 'report', icon: MapPin },
      ],
      features: ['Trapped-victim prioritization', 'Scene hazard update card', 'Equipment readiness and team ETA'],
    },
  };

  return base[role] || base.Citizen;
}

function rescueItemsForRole(role, rescues) {
  if (role === 'Citizen') return rescues.slice(0, 2);
  if (role === 'Hospital') return rescues.filter((item) => ['Critical', 'High'].includes(item.priority_label));
  if (role === 'Shelter') return rescues.filter((item) => item.condition === 'stable' || item.status === 'en route');
  if (role === 'Volunteer') return rescues.filter((item) => item.assigned_unit?.includes('Volunteer') || item.status === 'en route');
  if (role === 'Ambulance') return rescues.filter((item) => ['Critical', 'High'].includes(item.priority_label));
  return rescues;
}

function CommandView({
  metrics,
  disasters,
  rescues,
  priorityChart,
  disasterChart,
  trendChart,
  allocation,
  dashboardMode,
  setDashboardMode,
  alerts,
  alertDraft,
  setAlertDraft,
  sendAlert,
  reduceMotion,
}) {
  const chartOptions = {
    maintainAspectRatio: false,
    plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, usePointStyle: true } } },
    scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
  };

  return (
    <div className="view-stack">
      <section className="command-hero">
        <div>
          <p className="eyebrow">Common operating picture</p>
          <h2>Live risk and relief readiness</h2>
          <span>GIS map, resources, alerts, health capacity and field teams.</span>
        </div>
        <div className="hero-score-grid">
          <HeroScore label="People affected" value={metrics.affectedPeople} icon={Users} />
          <HeroScore label="Priority index" value={`${metrics.avgPriority}/100`} icon={TrendingUp} />
          <HeroScore label="Readiness" value={`${metrics.readinessScore}%`} icon={Zap} />
        </div>
      </section>

      <section className="dashboard-tabs" aria-label="Dashboard focus">
        {dashboardTabs.map(({ id, label, icon: Icon }) => (
          <button key={id} className={dashboardMode === id ? 'active' : ''} onClick={() => setDashboardMode(id)}>
            <Icon size={16} />
            {label}
          </button>
        ))}
      </section>

      <ResponseBoard disasters={disasters} rescues={rescues} reduceMotion={reduceMotion} />

      <section className="metrics-grid metrics-grid-5">
        <MetricTile icon={Activity} label="Active disasters" value={disasters.length} detail="Monitored hazard zones" />
        <MetricTile icon={HeartPulse} label="Critical rescues" value={metrics.critical} detail={`${metrics.pending} pending requests`} />
        <MetricTile icon={Ambulance} label="Ambulances ready" value={metrics.availableAmbulances} detail={`${metrics.assigned} units assigned/en route`} />
        <MetricTile icon={Home} label="Shelter capacity" value={metrics.shelterCapacity} detail={`${metrics.totalShelterCapacity} total relief slots`} />
        <MetricTile icon={Building2} label="Hospital beds" value={metrics.beds} detail={`${metrics.totalBeds} total beds tracked`} />
      </section>

      <section className="main-grid command-grid">
        <motion.div className="panel map-panel" layout transition={reduceMotion ? quickFade : softSpring}>
          <div className="panel-header">
            <div>
              <p>Live incident map</p>
              <h2>Reports, rescues and impact locations</h2>
            </div>
            <StatusPill value="Live GIS" />
          </div>
          <MapContainer center={[9.95, 76.35]} zoom={9} scrollWheelZoom={false} className="incident-map">
            <TileLayer attribution="&copy; OpenStreetMap contributors" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
            {disasters.map((item) => (
              <CircleMarker key={`d-${item.id}`} center={[item.latitude, item.longitude]} radius={12} pathOptions={{ color: '#dc2626', fillColor: '#dc2626', fillOpacity: 0.75 }}>
                <Popup>
                  <strong>{item.title}</strong>
                  <br />
                  {item.address}
                  <br />
                  AI damage: {item.label}
                </Popup>
              </CircleMarker>
            ))}
            {rescues.map((item) => (
              <CircleMarker key={`r-${item.id}`} center={[item.latitude, item.longitude]} radius={7} pathOptions={{ color: '#2563eb', fillColor: '#2563eb', fillOpacity: 0.85 }}>
                <Popup>
                  <strong>{item.victim_name}</strong>
                  <br />
                  Priority: {item.priority_label}
                </Popup>
              </CircleMarker>
            ))}
          </MapContainer>
        </motion.div>

        <DecisionStack allocation={allocation} rescues={rescues} disasters={disasters} />
      </section>

      <section className="analytics-wall">
        <PanelTitle eyebrow="Trend analytics" title="Response trend" />
        <div className="chart-box chart-box-wide">
          <Line data={trendChart} options={chartOptions} />
        </div>
      </section>

      <section className="split-grid split-grid-3">
        <div className="panel">
          <PanelTitle eyebrow="AI queue" title="Priority distribution" />
          <div className="chart-box">
            <Doughnut data={priorityChart} options={{ maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } }} />
          </div>
        </div>
        <div className="panel">
          <PanelTitle eyebrow="Hazard mix" title="Disasters by type" />
          <div className="chart-box">
            <Bar data={disasterChart} options={chartOptions} />
          </div>
        </div>
        <EarlyWarningPanel />
      </section>

      <section className="operations-grid">
        <ResourceReadinessPanel />
        <FieldTeamsPanel />
        <StandardsPanel />
        <AlertComposer alerts={alerts} draft={alertDraft} setDraft={setAlertDraft} onSubmit={sendAlert} />
      </section>
    </div>
  );
}

function ResponseBoard({ disasters, rescues, reduceMotion }) {
  const columns = getResponseBoardColumns(disasters, rescues);
  return (
    <section className="response-board" aria-label="Emergency response stages">
      {columns.map((column) => (
        <div className="response-column" key={column.id}>
          <div className="response-column-header">
            <div>
              <h2>{column.title}</h2>
              <span>{column.subtitle}</span>
            </div>
            <button type="button" aria-label={`Sort ${column.title}`}>
              {column.items.length}
              <ArrowUpDown size={13} />
            </button>
          </div>
          <div className="response-card-list">
            {column.items.map((item) => (
              <ResponseCard key={item.id} item={item} reduceMotion={reduceMotion} />
            ))}
          </div>
        </div>
      ))}
    </section>
  );
}

function ResponseCard({ item, reduceMotion }) {
  return (
    <motion.article
      className={`response-card ${item.dark ? 'dark-card' : ''}`}
      layout
      whileHover={reduceMotion ? undefined : { y: -3 }}
      transition={reduceMotion ? quickFade : softSpring}
    >
      <div className="response-card-title">
        <div>
          <h3>{item.title}</h3>
          <span>{item.kicker}</span>
        </div>
        <button type="button" aria-label={`More actions for ${item.title}`}>
          <MoreVertical size={16} />
        </button>
      </div>
      <p>{item.description}</p>
      <div className="response-card-meta">
        <span>
          <CalendarDays size={14} />
          {item.time}
        </span>
        <span>
          <MessageSquare size={14} />
          {item.updates}
        </span>
        <span>
          <Users size={14} />
          {item.people}
        </span>
      </div>
      <div className="response-card-footer">
        <StatusPill value={item.status} />
        <strong>{item.score}</strong>
      </div>
    </motion.article>
  );
}

function getResponseBoardColumns(disasters, rescues) {
  const reportCards = disasters.slice(0, 3).map((item) => ({
    id: `report-${item.id}`,
    title: item.title,
    kicker: item.disaster_type,
    description: `${item.address}. ${item.people_affected} people affected.`,
    time: item.created_at,
    updates: `${Math.max(1, Math.round(item.score / 18))} updates`,
    people: item.people_affected,
    status: item.label,
    score: `${item.score}/100`,
  }));

  const prioritizedCards = rescues
    .filter((item) => ['Critical', 'High'].includes(item.priority_label))
    .slice(0, 3)
    .map((item, index) => ({
      id: `priority-${item.id}`,
      title: item.victim_name,
      kicker: `${item.condition} condition`,
      description: item.notes,
      time: item.created_at,
      updates: `${item.trapped ? 5 : 2} notes`,
      people: item.people_count,
      status: item.priority_label,
      score: `${item.priority_score}/100`,
      dark: index === 0,
    }));

  const dispatchedCards = rescues
    .filter((item) => ['assigned', 'en route'].includes(item.status))
    .slice(0, 3)
    .map((item) => ({
      id: `dispatch-${item.id}`,
      title: item.assigned_unit || 'Dispatch pending',
      kicker: item.victim_name,
      description: item.notes,
      time: item.created_at,
      updates: item.status === 'en route' ? 'ETA live' : 'assigned',
      people: item.people_count,
      status: item.status,
      score: item.priority_label,
    }));

  const closedCards = [
    {
      id: 'closed-sitrep',
      title: 'Ward 14 SitRep',
      kicker: 'situation report',
      description: 'Road corridor verified, shelter route open, hospital handoff ready.',
      time: 'Now',
      updates: 'CAP draft',
      people: '1 ward',
      status: 'Live',
      score: 'Verified',
    },
    {
      id: 'closed-mutual-aid',
      title: 'Mutual-aid request',
      kicker: 'resource support',
      description: 'Requesting additional boats and family relief kits from partner agencies.',
      time: '15 min',
      updates: '2 partners',
      people: '4 assets',
      status: 'Active',
      score: 'Open',
    },
  ];

  return [
    { id: 'reported', title: 'Reported', subtitle: 'Incoming field reports', items: reportCards },
    { id: 'prioritized', title: 'Prioritized', subtitle: 'AI-ranked rescue needs', items: prioritizedCards },
    { id: 'dispatched', title: 'Dispatched', subtitle: 'Teams and vehicles moving', items: dispatchedCards },
    { id: 'coordinated', title: 'Coordinated', subtitle: 'Alerts, SitReps and aid', items: closedCards },
  ];
}

function HeroScore({ label, value, icon: Icon }) {
  return (
    <div className="hero-score">
      <Icon size={18} />
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function DecisionStack({ allocation, rescues, disasters }) {
  const topRescue = rescues[0];
  const topDisaster = disasters[0];
  return (
    <div className="decision-stack">
      <div className="panel decision-card">
        <div className="panel-header">
          <div>
            <p>AI allocation</p>
            <h2>Recommended next dispatch</h2>
          </div>
          <StatusPill value="Computed" />
        </div>
        <div className="allocation-grid">
          {Object.entries(allocation).map(([key, value]) => (
            <div key={key}>
              <span>{key.replace('_', ' ')}</span>
              <strong>{value}</strong>
            </div>
          ))}
        </div>
      </div>

      <div className="panel decision-card">
        <PanelTitle eyebrow="Next best action" title={topRescue ? topRescue.victim_name : 'No active rescue'} />
        <div className="action-brief">
          <Crosshair size={20} />
          <div>
            <strong>{topRescue ? `${topRescue.priority_label} priority rescue` : 'Queue clear'}</strong>
            <span>{topRescue ? `${topRescue.notes} Assigned unit: ${topRescue.assigned_unit || 'unassigned'}` : 'No high-priority queue item.'}</span>
          </div>
        </div>
        <div className="action-brief">
          <Navigation size={20} />
          <div>
            <strong>{topDisaster?.address || 'No active incident'}</strong>
            <span>{topDisaster ? `${topDisaster.people_affected} people affected, ${topDisaster.label} AI damage estimate` : 'No active incident.'}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function EarlyWarningPanel() {
  return (
    <section className="panel">
      <PanelTitle eyebrow="Early warning" title="Readiness pillars" />
      <div className="readiness-list">
        {earlyWarningPillars.map(({ name, score, detail, icon: Icon }) => (
          <div className="readiness-item" key={name}>
            <div className="readiness-heading">
              <span>
                <Icon size={16} />
                {name}
              </span>
              <strong>{score}%</strong>
            </div>
            <ProgressBar value={score} />
            <p>{detail}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function ResourceReadinessPanel() {
  return (
    <section className="panel">
      <PanelTitle eyebrow="Logistics" title="Resource inventory health" />
      <div className="inventory-list">
        {resourceInventory.map((item) => {
          const percent = Math.round((item.available / item.total) * 100);
          return (
            <div className="inventory-row" key={item.name}>
              <div>
                <strong>{item.name}</strong>
                <span>{item.available.toLocaleString()} {item.unit} available</span>
              </div>
              <div className="inventory-meter">
                <span>{percent}%</span>
                <ProgressBar value={percent} />
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function FieldTeamsPanel() {
  return (
    <section className="panel">
      <PanelTitle eyebrow="Field operations" title="Team progress and ETA" />
      <div className="team-list">
        {fieldTeams.map((team) => (
          <div className="team-row" key={team.name}>
            <div className="team-status-dot" />
            <div>
              <strong>{team.name}</strong>
              <span>{team.location}</span>
            </div>
            <StatusPill value={team.status} />
            <strong className="team-eta">{team.eta}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}

function StandardsPanel() {
  return (
    <section className="panel standards-panel">
      <PanelTitle eyebrow="Recommended capabilities" title="Command-center controls" />
      <div className="standards-list">
        {standardsFeatures.map((feature) => {
          const Icon = feature.icon;
          return (
            <div className="standard-feature" key={feature.label}>
              <Icon size={17} />
              <div>
                <strong>{feature.label}</strong>
                <span>{feature.detail}</span>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function AlertComposer({ alerts, draft, setDraft, onSubmit }) {
  return (
    <section className="panel alert-panel">
      <PanelTitle eyebrow="Public warning" title="Alert dissemination" />
      <form className="alert-form" onSubmit={onSubmit}>
        <div className="form-row form-row-2">
          <Input label="Audience" value={draft.audience} onChange={(value) => setDraft({ ...draft, audience: value })} required />
          <Input label="Channel" value={draft.channel} onChange={(value) => setDraft({ ...draft, channel: value })} required />
        </div>
        <Textarea label="Message" value={draft.message} onChange={(value) => setDraft({ ...draft, message: value })} required />
        <button className="primary-action" type="submit">
          <Send size={18} /> Send alert
        </button>
      </form>
      <div className="alert-feed">
        {alerts.slice(0, 3).map((alert) => (
          <div className="alert-feed-item" key={alert.id}>
            <Megaphone size={16} />
            <div>
              <strong>{alert.audience}</strong>
              <span>{alert.channel} - {alert.time}</span>
              <p>{alert.message}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function PanelTitle({ eyebrow, title }) {
  return (
    <div className="panel-header">
      <div>
        <p>{eyebrow}</p>
        <h2>{title}</h2>
      </div>
    </div>
  );
}

function ProgressBar({ value }) {
  return (
    <div className="progress-track" aria-label={`${value}%`}>
      <span style={{ width: `${Math.max(3, Math.min(100, value))}%` }} />
    </div>
  );
}

function ReportView({ draft, setDraft, onSubmit, rescueDraft, setRescueDraft, disasters, onRescueSubmit }) {
  return (
    <section className="form-grid">
      <form className="panel form-panel" onSubmit={onSubmit}>
        <div className="panel-header">
          <div>
            <p>Citizen report</p>
            <h2>Report a disaster</h2>
          </div>
        </div>
        <Input label="Title" value={draft.title} onChange={(value) => setDraft({ ...draft, title: value })} required />
        <div className="form-row">
          <Select label="Type" value={draft.disaster_type} options={disasterOptions} onChange={(value) => setDraft({ ...draft, disaster_type: value })} />
          <Select label="Severity hint" value={draft.severity_hint} options={severityOptions} onChange={(value) => setDraft({ ...draft, severity_hint: value })} />
        </div>
        <Input label="Address" value={draft.address} onChange={(value) => setDraft({ ...draft, address: value })} required />
        <Textarea label="Description" value={draft.description} onChange={(value) => setDraft({ ...draft, description: value })} required />
        <div className="form-row">
          <Input label="Latitude" type="number" value={draft.latitude} onChange={(value) => setDraft({ ...draft, latitude: value })} />
          <Input label="Longitude" type="number" value={draft.longitude} onChange={(value) => setDraft({ ...draft, longitude: value })} />
          <Input label="People affected" type="number" value={draft.people_affected} onChange={(value) => setDraft({ ...draft, people_affected: value })} />
        </div>
        <button className="primary-action" type="submit">
          <MapPin size={18} /> Submit disaster report
        </button>
      </form>

      <form className="panel form-panel" onSubmit={onRescueSubmit}>
        <div className="panel-header">
          <div>
            <p>Emergency request</p>
            <h2>Request rescue</h2>
          </div>
        </div>
        <Select label="Linked disaster" value={rescueDraft.disaster_id} options={disasters.map((item) => ({ label: item.title, value: item.id }))} onChange={(value) => setRescueDraft({ ...rescueDraft, disaster_id: value })} />
        <Input label="Victim name" value={rescueDraft.victim_name} onChange={(value) => setRescueDraft({ ...rescueDraft, victim_name: value })} required />
        <div className="form-row">
          <Input label="Age" type="number" value={rescueDraft.victim_age} onChange={(value) => setRescueDraft({ ...rescueDraft, victim_age: value })} />
          <Input label="People count" type="number" value={rescueDraft.people_count} onChange={(value) => setRescueDraft({ ...rescueDraft, people_count: value })} />
          <Select label="Condition" value={rescueDraft.condition} options={conditionOptions} onChange={(value) => setRescueDraft({ ...rescueDraft, condition: value })} />
        </div>
        <label className="toggle-row">
          <input type="checkbox" checked={rescueDraft.trapped} onChange={(event) => setRescueDraft({ ...rescueDraft, trapped: event.target.checked })} />
          Victim is trapped
        </label>
        <Input label="Vulnerable people" type="number" value={rescueDraft.vulnerable_people} onChange={(value) => setRescueDraft({ ...rescueDraft, vulnerable_people: value })} />
        <Textarea label="Notes" value={rescueDraft.notes} onChange={(value) => setRescueDraft({ ...rescueDraft, notes: value })} />
        <button className="primary-action" type="submit">
          <HeartPulse size={18} /> Submit rescue request
        </button>
      </form>
    </section>
  );
}

function RescueView({ role, rescues, disasters, onAssign }) {
  const canAssign = assignCapableRoles.has(role);
  const title = role === 'Citizen' ? 'My rescue tracking' : role === 'Hospital' ? 'Incoming triage requests' : role === 'Volunteer' ? 'Volunteer tasks' : 'Rescue requests';
  const eyebrow = role === 'Citizen' ? 'Live status' : role === 'Hospital' ? 'Hospital triage' : role === 'Volunteer' ? 'Assignment queue' : 'AI ranked queue';
  const actionLabel = canAssign ? 'Assign' : role === 'Citizen' ? 'Track' : role === 'Hospital' ? 'Triage' : role === 'Volunteer' ? 'Check in' : 'View';

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p>{eyebrow}</p>
          <h2>{title}</h2>
        </div>
        <StatusPill value={`${rescues.length} active`} />
      </div>
      <div className="table-responsive">
        <table className="table align-middle command-table">
          <thead>
            <tr>
              <th>Victim</th>
              <th>Incident</th>
              <th>Risk</th>
              <th>Status</th>
              <th>Assigned unit</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {rescues.map((item) => (
              <tr key={item.id}>
                <td>
                  <strong>{item.victim_name}</strong>
                  <span>{item.people_count} people - age {item.victim_age}</span>
                </td>
                <td>{disasters.find((disaster) => disaster.id === Number(item.disaster_id))?.title || 'Unlinked incident'}</td>
                <td>
                  <StatusPill value={item.priority_label} />
                  <span className="score-text">{item.priority_score}/100</span>
                </td>
                <td>
                  <StatusPill value={item.status} />
                </td>
                <td>{item.assigned_unit || 'Unassigned'}</td>
                <td>
                  <button className="compact-button" disabled={canAssign && item.status === 'assigned'} onClick={() => canAssign && onAssign(item.id)}>
                    {actionLabel}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function FacilitiesView({ role, facilities, updateHospital, updateShelter }) {
  const showHospitals = ['Admin', 'Hospital', 'Ambulance', 'Police', 'Fire Service'].includes(role);
  const showShelters = ['Admin', 'Shelter', 'NGO', 'Citizen', 'Volunteer'].includes(role);
  const showAmbulances = ['Admin', 'Ambulance', 'Hospital', 'Police', 'Fire Service'].includes(role);

  return (
    <section className="view-stack">
      <div className="facility-grid">
        {showHospitals && (
          <FacilityPanel title={role === 'Hospital' ? 'My hospital capacity' : 'Hospitals'} icon={Building2}>
            {facilities.hospitals.map((item) => (
              <div className="facility-item" key={item.id}>
                <div>
                  <strong>{item.name}</strong>
                  <span>{item.available_beds}/{item.total_beds} beds - ICU {item.icu_beds}</span>
                </div>
                <div className="stepper">
                  <button onClick={() => updateHospital(item.id, -5)}>-</button>
                  <strong>{item.available_beds}</strong>
                  <button onClick={() => updateHospital(item.id, 5)}>+</button>
                </div>
              </div>
            ))}
          </FacilityPanel>
        )}
        {showShelters && (
          <FacilityPanel title={role === 'Shelter' ? 'My shelter capacity' : 'Shelters'} icon={Home}>
            {facilities.shelters.map((item) => (
              <div className="facility-item" key={item.id}>
                <div>
                  <strong>{item.name}</strong>
                  <span>{item.available_capacity}/{item.total_capacity} slots - {item.medical_support ? 'medical support' : 'basic support'}</span>
                </div>
                <div className="stepper">
                  <button onClick={() => updateShelter(item.id, -10)}>-</button>
                  <strong>{item.available_capacity}</strong>
                  <button onClick={() => updateShelter(item.id, 10)}>+</button>
                </div>
              </div>
            ))}
          </FacilityPanel>
        )}
        {showAmbulances && (
          <FacilityPanel title={role === 'Ambulance' ? 'My ambulance status' : 'Ambulances'} icon={Ambulance}>
            {facilities.ambulances.map((item) => (
              <div className="facility-item" key={item.id}>
                <div>
                  <strong>{item.vehicle_number}</strong>
                  <span>{item.driver_name}</span>
                </div>
                <StatusPill value={item.status} />
              </div>
            ))}
          </FacilityPanel>
        )}
      </div>
    </section>
  );
}

function FacilityPanel({ title, icon: Icon, children }) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div className="facility-title">
          <Icon size={20} />
          <h2>{title}</h2>
        </div>
      </div>
      <div className="facility-list">{children}</div>
    </section>
  );
}

function Input({ label, value, onChange, type = 'text', required = false }) {
  return (
    <label className="form-field">
      <span>{label}</span>
      <input className="form-control" type={type} value={value} required={required} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

function Textarea({ label, value, onChange, required = false }) {
  return (
    <label className="form-field">
      <span>{label}</span>
      <textarea className="form-control" rows="4" value={value} required={required} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

function Select({ label, value, options, onChange }) {
  return (
    <label className="form-field">
      <span>{label}</span>
      <select className="form-select" value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => {
          const normalized = typeof option === 'string' ? { label: option, value: option } : option;
          return (
            <option key={normalized.value} value={normalized.value}>
              {normalized.label}
            </option>
          );
        })}
      </select>
    </label>
  );
}

function roleMessage(role) {
  const messages = {
    Citizen: 'Fast reporting and rescue tracking are prioritized.',
    Hospital: 'Capacity updates are visible to command staff.',
    Shelter: 'Relief camp availability feeds allocation decisions.',
    Ambulance: 'Dispatch status keeps rescue tracking current.',
    NGO: 'Distribution and volunteer coordination are emphasized.',
    Volunteer: 'Assignment readiness appears in admin analytics.',
    Police: 'Incident control and queue review are available.',
    'Fire Service': 'Fire and rescue assignments are highlighted.',
    Admin: 'All dashboards, queues, and facilities are visible.',
  };
  return messages[role] || messages.Admin;
}
