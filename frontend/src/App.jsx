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
  CircleCheck,
  ClipboardList,
  CloudOff,
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
  RefreshCw,
  Route,
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
import {
  api,
  beginMfaSetup,
  changePassword,
  completeMfaLogin,
  confirmMfaSetup,
  disableMfa,
  getMfaStatus,
  isNetworkFailure,
  listSessions,
  login,
  logout,
  openDemoSession,
  regenerateMfaRecoveryCodes,
  register,
  revokeSession,
  restoreSession,
} from './services/api.js';
import { initialDisasters, initialFacilities, initialRescues, initialResponseHub, roles } from './services/mockData.js';

ChartJS.register(ArcElement, BarElement, CategoryScale, Filler, Legend, LineElement, LinearScale, PointElement, Tooltip);

const disasterOptions = ['flood', 'earthquake', 'cyclone', 'landslide', 'fire'];
const severityOptions = ['low', 'medium', 'high', 'critical'];
const conditionOptions = ['stable', 'injured', 'critical', 'unconscious', 'bleeding'];
const filterStatusOptions = ['pending', 'assigned', 'en route', 'triage', 'rescued', 'active', 'monitoring'];
const sortModes = ['priority', 'newest', 'people'];
const sortLabels = {
  priority: 'Sort: risk',
  newest: 'Sort: newest',
  people: 'Sort: people',
};
const dashboardTabs = [
  { id: 'overview', label: 'Overview', icon: Gauge },
  { id: 'response', label: 'Response', icon: Siren },
  { id: 'health', label: 'Health', icon: HeartPulse },
  { id: 'logistics', label: 'Logistics', icon: Package },
];
const softSpring = { type: 'spring', stiffness: 420, damping: 34, mass: 0.8 };
const quickFade = { duration: 0.18, ease: [0.22, 1, 0.36, 1] };

const standardsFeatures = [
  { label: 'CAP alert templates', detail: 'All-hazard public warnings across SMS, siren, radio and web.', icon: Megaphone },
  { label: 'Incident command roles', detail: 'Clear ownership for command, operations, logistics and medical.', icon: RadioTower },
  { label: 'Typed resource inventory', detail: 'Track boats, ambulances, kits, shelters and trained people.', icon: Package },
  { label: 'Mutual-aid requests', detail: 'Escalate shortages to partner NGOs and nearby agencies.', icon: Users },
  { label: 'Situation reports', detail: 'Share verified updates, constraints and next operational needs.', icon: ClipboardList },
];

const demoResponseTrend = [
  { time: '08:00', reports: 4, rescued: 1 },
  { time: '09:00', reports: 9, rescued: 3 },
  { time: '10:00', reports: 14, rescued: 6 },
  { time: '11:00', reports: 18, rescued: 10 },
  { time: '12:00', reports: 24, rescued: 13 },
  { time: '13:00', reports: 27, rescued: 17 },
];

const initialAlerts = [
  { id: 1, audience: 'Ward 176 - Velachery', channel: 'SMS + radio', message: 'Move to Velachery Govt School Relief Camp. Avoid the lake bund service road.', time: '8 min ago' },
  { id: 2, audience: 'Chennai hospital network', channel: 'Ops dashboard', message: 'Prepare 35 emergency beds for flood and cyclone response corridors.', time: '24 min ago' },
];

const roleNavigation = {
  Admin: [
    { id: 'command', label: 'Command', icon: RadioTower },
    { id: 'report', label: 'Report Disaster', icon: MapPin },
    { id: 'rescue', label: 'Rescue Queue', icon: HeartPulse },
    { id: 'facilities', label: 'Facilities', icon: Building2 },
    { id: 'coordination', label: 'Relief Coordination', icon: Package },
    { id: 'access', label: 'User Access', icon: UserRound },
    { id: 'setup', label: 'Operational Setup', icon: SlidersHorizontal },
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
    { id: 'coordination', label: 'Relief Coordination', icon: Users },
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

const assignCapableRoles = new Set(['Admin', 'Police', 'Fire Service', 'NGO']);
const OFFLINE_QUEUE_KEY = 'resq-command-offline-queue';
const OFFLINE_QUEUE_TTL_MS = 24 * 60 * 60 * 1000;
const OFFLINE_QUEUE_LIMIT = 50;
const DEMO_ENABLED = import.meta.env.VITE_DEMO_MODE === 'true';
const emptyFacilities = { hospitals: [], shelters: [], ambulances: [] };
const emptyResponseHub = {
  emergency_hotline: '112',
  news_updates: [],
  welfare_checks: [],
  hospital_notifications: [],
  supply_requests: [],
  campaigns: [],
  dispatches: [],
  responder_units: [],
};
const emptyAuthDraft = { name: '', email: '', phone: '', password: '', password_confirmation: '', role: 'Citizen' };
const emptyPasswordDraft = { current_password: '', new_password: '', new_password_confirmation: '' };
const emptyProvisionDraft = {
  name: '',
  email: '',
  phone: '',
  role: 'Hospital',
  password: '',
  password_confirmation: '',
  organization_name: '',
  facility_id: 'new',
  facility: {
    name: '',
    address: '',
    latitude: '',
    longitude: '',
    contact_phone: '',
    total_beds: '',
    available_beds: '',
    icu_beds: '',
    emergency_capacity: '',
    total_capacity: '',
    available_capacity: '',
    food_available: true,
    medical_support: false,
    vehicle_number: '',
    driver_name: '',
    hospital_id: '',
  },
};

export default function App() {
  const reduceMotion = useReducedMotion();
  const [activeRole, setActiveRole] = useState('Citizen');
  const [activeView, setActiveView] = useState('command');
  const [dashboardMode, setDashboardMode] = useState('overview');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortMode, setSortMode] = useState('priority');
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({ type: 'all', severity: 'all', status: 'all' });
  const [selectedRescueId, setSelectedRescueId] = useState(null);
  const [operatorNotice, setOperatorNotice] = useState(DEMO_ENABLED ? 'India-wide emergency demo data loaded' : 'Sign in to access live emergency operations');
  const [connectionState, setConnectionState] = useState('connecting');
  const [currentUser, setCurrentUser] = useState(null);
  const [sessionMode, setSessionMode] = useState(DEMO_ENABLED ? 'demo' : 'checking');
  const [showAccountPanel, setShowAccountPanel] = useState(!DEMO_ENABLED);
  const [authMode, setAuthMode] = useState('login');
  const [authDraft, setAuthDraft] = useState(emptyAuthDraft);
  const [passwordDraft, setPasswordDraft] = useState(emptyPasswordDraft);
  const [mfaChallenge, setMfaChallenge] = useState({ token: '', code: '' });
  const [mfaSession, setMfaSession] = useState({ required: false, enabled: false, verified: false, setup_required: false, recovery_codes_remaining: 0 });
  const [mfaSetup, setMfaSetup] = useState({ current_password: '', code: '', secret: '', provisioning_uri: '', recovery_codes: [] });
  const [mfaAction, setMfaAction] = useState({ current_password: '', code: '' });
  const [accountSessions, setAccountSessions] = useState([]);
  const [managedUsers, setManagedUsers] = useState([]);
  const [provisionDraft, setProvisionDraft] = useState(emptyProvisionDraft);
  const [resetDraft, setResetDraft] = useState({ user_id: '', admin_password: '', new_password: '', password_confirmation: '' });
  const [mfaResetDraft, setMfaResetDraft] = useState({ user_id: '', admin_password: '' });
  const [resourceDraft, setResourceDraft] = useState({ name: '', category: 'food', unit: 'units', available_quantity: 0, storage_location: '' });
  const [responderDraft, setResponderDraft] = useState({ name: '', unit_type: 'professional rescue', skills: '', contact_phone: '', latitude: '', longitude: '' });
  const [campaignDraft, setCampaignDraft] = useState({ disaster_id: '', title: '', description: '', goal_amount: '', currency: 'INR', organizer: '' });
  const [pendingOperations, setPendingOperations] = useState(() => readOfflineQueue());
  const [routeResult, setRouteResult] = useState(null);
  const [coordinationData, setCoordinationData] = useState({ volunteers: [], distributions: [], assignments: [] });
  const [disasters, setDisasters] = useState(() => (DEMO_ENABLED ? initialDisasters : []));
  const [rescues, setRescues] = useState(() => (DEMO_ENABLED ? initialRescues : []));
  const [facilities, setFacilities] = useState(() => (DEMO_ENABLED ? initialFacilities : emptyFacilities));
  const [resources, setResources] = useState([]);
  const [alerts, setAlerts] = useState(() => (DEMO_ENABLED ? initialAlerts : []));
  const [responseHub, setResponseHub] = useState(() => (DEMO_ENABLED ? initialResponseHub : emptyResponseHub));
  const [alertDraft, setAlertDraft] = useState({
    audience: DEMO_ENABLED ? 'Chennai Zone 13 - Adyar / Velachery' : '',
    channel: DEMO_ENABLED ? 'SMS + siren + volunteer relay' : '',
    message: DEMO_ENABLED ? 'Heavy rainfall and waterlogging expected. Move vulnerable residents to the nearest open relief camp.' : '',
    instruction: DEMO_ENABLED ? 'Use the marked evacuation corridor, assist children and older adults, and acknowledge this warning when safe.' : '',
  });
  const [incidentDraft, setIncidentDraft] = useState({
    title: '',
    disaster_type: 'flood',
    address: '',
    description: '',
    latitude: DEMO_ENABLED ? 12.9798 : '',
    longitude: DEMO_ENABLED ? 80.2209 : '',
    people_affected: DEMO_ENABLED ? 25 : 1,
    severity_hint: 'medium',
  });
  const [rescueDraft, setRescueDraft] = useState({
    disaster_id: '',
    victim_name: '',
    victim_age: '',
    people_count: 1,
    condition: 'injured',
    trapped: false,
    vulnerable_people: 0,
    latitude: DEMO_ENABLED ? 12.9806 : '',
    longitude: DEMO_ENABLED ? 80.2194 : '',
    notes: '',
  });
  const [distributionDraft, setDistributionDraft] = useState({ resource_id: '', disaster_id: '', quantity: DEMO_ENABLED ? 25 : 1, destination: DEMO_ENABLED ? 'Velachery Govt School Relief Camp' : '' });
  const [volunteerDraft, setVolunteerDraft] = useState({ volunteer_id: '', disaster_id: '', task: DEMO_ENABLED ? 'Support evacuation and first-aid desk' : '' });
  const [welfareDraft, setWelfareDraft] = useState({ disaster_id: '', relative_name: '', relative_phone: '', relationship: '', last_known_location: '', requester_phone: '', consent_to_contact: false });
  const [supplyDraft, setSupplyDraft] = useState({ disaster_id: '', category: 'food and water', description: '', people_count: 1, urgency: 'high', contact_phone: '', latitude: DEMO_ENABLED ? 12.9806 : '', longitude: DEMO_ENABLED ? 80.2194 : '', location_accuracy: '', location_consent: false });
  const [donationDraft, setDonationDraft] = useState({ campaign_id: '', donor_name: '', donor_email: '', amount: '', anonymous: false, message: '' });
  const [newsDraft, setNewsDraft] = useState({ disaster_id: '', headline: '', summary: '', source_name: '', stream_url: '', state: '', district: '', is_live: true });

  const readinessPillars = useMemo(() => {
    const completeDisasters = disasters.filter((item) => (
      item.address && Number.isFinite(Number(item.latitude)) && Number.isFinite(Number(item.longitude))
    )).length;
    const completeAlerts = alerts.filter((item) => item.audience && item.channel && item.message && item.instruction).length;
    const preparednessChecks = [
      facilities.hospitals.length > 0,
      facilities.shelters.length > 0,
      facilities.ambulances.length > 0,
      resources.length > 0,
    ];
    return [
      {
        name: 'Risk knowledge',
        score: disasters.length ? Math.round((completeDisasters / disasters.length) * 100) : 0,
        detail: disasters.length ? `${completeDisasters} of ${disasters.length} incidents have mapped locations` : 'No live incidents have been recorded',
        icon: Database,
      },
      {
        name: 'Monitoring',
        score: connectionState === 'online' ? 100 : 0,
        detail: connectionState === 'online' ? 'Live operations API and database are connected' : 'Live operations connection is unavailable',
        icon: Wifi,
      },
      {
        name: 'Communication',
        score: alerts.length ? Math.round((completeAlerts / alerts.length) * 100) : 0,
        detail: alerts.length ? `${completeAlerts} of ${alerts.length} active alerts contain complete instructions` : 'No active public warnings have been issued',
        icon: Megaphone,
      },
      {
        name: 'Preparedness',
        score: Math.round((preparednessChecks.filter(Boolean).length / preparednessChecks.length) * 100),
        detail: `${preparednessChecks.filter(Boolean).length} of ${preparednessChecks.length} facility and inventory groups configured`,
        icon: ClipboardList,
      },
    ];
  }, [alerts, connectionState, disasters, facilities, resources]);

  const metrics = useMemo(() => {
    const pending = rescues.filter((item) => item.status === 'pending').length;
    const assigned = rescues.filter((item) => ['assigned', 'en route', 'triage'].includes(item.status)).length;
    const critical = rescues.filter((item) => item.priority_label === 'Critical').length;
    const beds = facilities.hospitals.reduce((sum, item) => sum + item.available_beds, 0);
    const totalBeds = facilities.hospitals.reduce((sum, item) => sum + item.total_beds, 0);
    const shelterCapacity = facilities.shelters.reduce((sum, item) => sum + item.available_capacity, 0);
    const totalShelterCapacity = facilities.shelters.reduce((sum, item) => sum + item.total_capacity, 0);
    const availableAmbulances = facilities.ambulances.filter((item) => item.status === 'available').length;
    const affectedPeople = disasters.reduce((sum, item) => sum + Number(item.people_affected || 0), 0);
    const avgPriority = Math.round(rescues.reduce((sum, item) => sum + item.priority_score, 0) / Math.max(1, rescues.length));
    const readinessScore = Math.round(readinessPillars.reduce((sum, item) => sum + item.score, 0) / readinessPillars.length);
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
  }, [rescues, facilities, disasters, readinessPillars]);

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

  const trendChart = useMemo(() => {
    const responseTrend = DEMO_ENABLED ? demoResponseTrend : buildHourlyResponseTrend(disasters, rescues);
    return {
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
    };
  }, [disasters, rescues]);

  const disasterLookup = useMemo(() => new Map(disasters.map((item) => [Number(item.id), item])), [disasters]);
  const filteredDisasters = useMemo(
    () => filterAndSortDisasters(disasters, { searchQuery, filters, sortMode }),
    [disasters, searchQuery, filters, sortMode],
  );
  const sortedRescues = useMemo(
    () => filterAndSortRescues(rescues, disasterLookup, { searchQuery, filters, sortMode }),
    [rescues, disasterLookup, searchQuery, filters, sortMode],
  );
  const activeFilterCount = Object.values(filters).filter((value) => value !== 'all').length;
  const filterSummary = searchQuery.trim() || activeFilterCount ? `${filteredDisasters.length} reports, ${sortedRescues.length} rescues shown` : 'All India operations';
  const selectedDisaster = filteredDisasters.find((item) => Number(item.id) === Number(rescueDraft.disaster_id)) || disasters.find((item) => Number(item.id) === Number(rescueDraft.disaster_id)) || disasters[0];
  const allocation = selectedDisaster
    ? allocateResources({
        severity: sortedRescues[0]?.priority_label || selectedDisaster.label || 'Medium',
        people_count: selectedDisaster.people_affected || 1,
        disaster_type: selectedDisaster.disaster_type,
      })
    : { ambulances: 0, rescue_teams: 0, volunteers: 0, food_packets: 0, medicine_kits: 0, shelter_slots: 0 };
  const activeTopbar = roleTopbar[activeRole] || roleTopbar.Admin;
  const activeNavigation = useMemo(
    () => [
      ...(roleNavigation[activeRole] || roleNavigation.Admin),
      { id: 'response-hub', label: activeRole === 'Citizen' ? 'Family & Aid' : 'Response Hub', icon: RadioTower },
    ],
    [activeRole],
  );
  const visibleActiveView = activeNavigation.some((item) => item.id === activeView) ? activeView : 'command';
  const currentUserId = currentUser?.id;
  const currentUserName = currentUser?.name;
  const passwordChangeRequired = Boolean(currentUser?.password_change_required);
  const visibleRescues = rescueItemsForRole(activeRole, sortedRescues);

  useEffect(() => {
    if (DEMO_ENABLED) return;
    let cancelled = false;
    restoreSession()
      .then((session) => {
        if (cancelled) return;
        const { user } = session;
        setCurrentUser(user);
        setActiveRole(user.role);
        setSessionMode('account');
        setMfaSession({
          required: Boolean(user.mfa_required),
          enabled: Boolean(user.mfa_enabled),
          verified: Boolean(session.mfa_verified),
          setup_required: Boolean(session.mfa_setup_required),
          recovery_codes_remaining: 0,
        });
        const passwordRequired = Boolean(user.password_change_required);
        setShowAccountPanel(passwordRequired || Boolean(session.mfa_setup_required));
        setOperatorNotice(
          passwordRequired
            ? 'Replace your temporary password to continue.'
            : session.mfa_setup_required
              ? 'Set up multi-factor authentication to continue.'
              : `${user.name} session restored`,
        );
      })
      .catch(() => {
        if (cancelled) return;
        setSessionMode('account');
        setShowAccountPanel(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    function sessionExpired() {
      localStorage.removeItem(OFFLINE_QUEUE_KEY);
      setPendingOperations([]);
      setCurrentUser(null);
      setAuthDraft(emptyAuthDraft);
      setPasswordDraft(emptyPasswordDraft);
      setMfaChallenge({ token: '', code: '' });
      setMfaSession({ required: false, enabled: false, verified: false, setup_required: false, recovery_codes_remaining: 0 });
      setMfaSetup({ current_password: '', code: '', secret: '', provisioning_uri: '', recovery_codes: [] });
      setMfaAction({ current_password: '', code: '' });
      setAccountSessions([]);
      setProvisionDraft({ ...emptyProvisionDraft, facility: { ...emptyProvisionDraft.facility } });
      setResetDraft({ user_id: '', admin_password: '', new_password: '', password_confirmation: '' });
      setMfaResetDraft({ user_id: '', admin_password: '' });
      setSessionMode(DEMO_ENABLED ? 'demo' : 'account');
      setShowAccountPanel(!DEMO_ENABLED);
      setActiveRole('Citizen');
      setOperatorNotice('Your session expired. Sign in again to continue.');
    }
    window.addEventListener('resq:session-expired', sessionExpired);
    return () => window.removeEventListener('resq:session-expired', sessionExpired);
  }, []);

  useEffect(() => {
    if (sessionMode !== 'account' || !currentUserId || passwordChangeRequired) return;
    let cancelled = false;
    getMfaStatus()
      .then((status) => {
        if (!cancelled) setMfaSession(status);
      })
      .catch((error) => {
        if (!cancelled) setOperatorNotice(`MFA status could not be loaded: ${error.message}`);
      });
    return () => {
      cancelled = true;
    };
  }, [sessionMode, currentUserId, passwordChangeRequired]);

  useEffect(() => {
    if (
      !showAccountPanel
      || sessionMode !== 'account'
      || !currentUserId
      || passwordChangeRequired
      || mfaSession.setup_required
    ) {
      return;
    }
    let cancelled = false;
    listSessions()
      .then(({ sessions }) => {
        if (!cancelled) setAccountSessions(sessions);
      })
      .catch((error) => {
        if (!cancelled) setOperatorNotice(`Active sessions could not be loaded: ${error.message}`);
      });
    return () => {
      cancelled = true;
    };
  }, [showAccountPanel, sessionMode, currentUserId, passwordChangeRequired, mfaSession.setup_required]);

  useEffect(() => {
    if (visibleActiveView !== 'access' || currentUser?.role !== 'Admin') return;
    let cancelled = false;
    api.adminUsers()
      .then(({ users }) => {
        if (!cancelled) setManagedUsers(users);
      })
      .catch((error) => {
        if (!cancelled) setOperatorNotice(`User access list could not be loaded: ${error.message}`);
      });
    return () => {
      cancelled = true;
    };
  }, [visibleActiveView, currentUser]);

  useEffect(() => {
    let cancelled = false;
    async function connect() {
      if (
        sessionMode === 'checking'
        || (sessionMode === 'account' && (!currentUserId || passwordChangeRequired || mfaSession.setup_required))
      ) return;
      setConnectionState('connecting');
      try {
        const session = sessionMode === 'demo'
          ? await openDemoSession(activeRole)
          : { user: { id: currentUserId, name: currentUserName } };
        await flushOfflineQueue();
        const [snapshot, coordination] = await Promise.all([
          api.bootstrap(),
          ['Admin', 'NGO'].includes(activeRole) ? api.coordination() : Promise.resolve(null),
        ]);
        if (cancelled) return;
        if (sessionMode === 'demo') setCurrentUser(session.user);
        setDisasters(snapshot.disasters.map(normalizeDisaster));
        setRescues(snapshot.rescue_requests);
        setFacilities(snapshot.facilities);
        setResources(snapshot.resources || []);
        if (coordination) {
          setCoordinationData(coordination);
          alignOperationalDrafts(snapshot, coordination);
        }
        setAlerts(snapshot.alerts.map(normalizeAlert));
        if (!coordination) alignOperationalDrafts(snapshot);
        setResponseHub(snapshot.response_hub || (DEMO_ENABLED ? initialResponseHub : emptyResponseHub));
        setConnectionState('online');
        setOperatorNotice(`${session.user.name} connected to the live response API${sessionMode === 'demo' ? ' in demo mode' : ''}`);
      } catch (error) {
        if (cancelled) return;
        setConnectionState('offline');
        setOperatorNotice(`Offline-ready local mode active: ${error.message}`);
      }
    }
    connect();
    return () => {
      cancelled = true;
    };
  }, [activeRole, sessionMode, passwordChangeRequired, mfaSession.setup_required, currentUserId, currentUserName]);

  useEffect(() => {
    function reconnect() {
      if (sessionMode === 'account' && (passwordChangeRequired || mfaSession.setup_required)) return;
      if (navigator.onLine) {
        (sessionMode === 'demo' ? openDemoSession(activeRole) : Promise.resolve())
          .then(() => flushOfflineQueue())
          .then(() => Promise.all([
            api.bootstrap(),
            ['Admin', 'NGO'].includes(activeRole) ? api.coordination() : Promise.resolve(null),
          ]))
          .then(([snapshot, coordination]) => {
            setDisasters(snapshot.disasters.map(normalizeDisaster));
            setRescues(snapshot.rescue_requests);
            setFacilities(snapshot.facilities);
            setResources(snapshot.resources || []);
            if (coordination) {
              setCoordinationData(coordination);
              alignOperationalDrafts(snapshot, coordination);
            }
            setAlerts(snapshot.alerts.map(normalizeAlert));
            if (!coordination) alignOperationalDrafts(snapshot);
            setResponseHub(snapshot.response_hub || (DEMO_ENABLED ? initialResponseHub : emptyResponseHub));
            setConnectionState('online');
            return flushOfflineQueue();
          })
          .catch(() => setConnectionState('offline'));
      } else {
        setConnectionState('offline');
      }
    }
    window.addEventListener('online', reconnect);
    window.addEventListener('offline', reconnect);
    return () => {
      window.removeEventListener('online', reconnect);
      window.removeEventListener('offline', reconnect);
    };
  }, [activeRole, sessionMode, passwordChangeRequired, mfaSession.setup_required]);

  async function submitIncident(event) {
    event.preventDefault();
    const assessment = estimateDamage(incidentDraft);
    const optimistic = {
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
    let next = optimistic;
    let queuedOffline = false;
    try {
      const response = await api.createDisaster(incidentDraft);
      next = { ...response.disaster, score: response.damage_estimation.score, label: response.damage_estimation.label };
      setRescueDraft((current) => ({ ...current, disaster_id: current.disaster_id || next.id }));
      setWelfareDraft((current) => ({ ...current, disaster_id: current.disaster_id || next.id }));
      setSupplyDraft((current) => ({ ...current, disaster_id: current.disaster_id || next.id }));
      setNewsDraft((current) => ({ ...current, disaster_id: current.disaster_id || next.id }));
      setConnectionState('online');
    } catch (error) {
      if (!isNetworkFailure(error)) {
        setOperatorNotice(`Report rejected: ${error.message}`);
        return;
      }
      queueOfflineOperation('disaster', incidentDraft);
      next = { ...optimistic, sync_status: 'queued' };
      queuedOffline = true;
      setConnectionState('offline');
    }
    setDisasters((items) => [next, ...items]);
    setIncidentDraft({ ...incidentDraft, title: '', address: '', description: '', people_affected: DEMO_ENABLED ? 25 : 1 });
    setOperatorNotice(
      queuedOffline
        ? `${assessment.label} ${incidentDraft.disaster_type} report saved on this device and queued for reconnection`
        : `${assessment.label} ${incidentDraft.disaster_type} report added to the live national command view`,
    );
    setActiveView('command');
  }

  async function submitRescue(event) {
    event.preventDefault();
    const disaster = disasters.find((item) => Number(item.id) === Number(rescueDraft.disaster_id));
    const priority = prioritizeRescue(rescueDraft, disaster?.disaster_type);
    const optimistic = {
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
    let next = optimistic;
    let queuedOffline = false;
    try {
      const response = await api.createRescue(rescueDraft);
      next = response.rescue_request;
      const allocated = [response.automatic_allocation?.rescue_unit?.name, response.automatic_allocation?.volunteer?.name, response.automatic_allocation?.ambulance?.vehicle_number].filter(Boolean).join(' + ');
      if (allocated) setOperatorNotice(`${priority.label} request auto-dispatched to ${allocated}; receiving hospital alerted`);
      setConnectionState('online');
    } catch (error) {
      if (!isNetworkFailure(error)) {
        setOperatorNotice(`Rescue request rejected: ${error.message}`);
        return;
      }
      queueOfflineOperation('rescue', rescueDraft);
      next = { ...optimistic, sync_status: 'queued' };
      queuedOffline = true;
      setConnectionState('offline');
    }
    setRescues((items) => [next, ...items]);
    setRescueDraft({ ...rescueDraft, victim_name: '', notes: '', trapped: false });
    setSelectedRescueId(next.id);
    if (!next.assigned_unit) {
      setOperatorNotice(
        queuedOffline
          ? `${priority.label} rescue request saved on this device and queued for reconnection`
          : `${priority.label} rescue request created for ${next.victim_name}`,
      );
    }
    setActiveView('rescue');
  }

  async function sendAlert(event) {
    event.preventDefault();
    try {
      const response = await api.createAlert({
        audience: alertDraft.audience,
        channels: alertDraft.channel,
        message: alertDraft.message,
        instruction: alertDraft.instruction,
        event: 'Multi-hazard public warning',
      });
      const next = normalizeAlert(response.alert);
      setAlerts((items) => [next, ...items]);
      setAlertDraft({ ...alertDraft, message: '', instruction: '' });
      setConnectionState('online');
      setOperatorNotice(`Authoritative alert sent to ${next.audience} by ${next.channel}`);
    } catch (error) {
      setOperatorNotice(`Alert was not sent: ${error.message}`);
    }
  }

  async function handleRescueAction(id, role = activeRole) {
    const rescue = rescues.find((item) => item.id === id);
    if (!rescue) return;
    setSelectedRescueId(id);

    if (assignCapableRoles.has(role)) {
      const disaster = disasterLookup.get(Number(rescue.disaster_id));
      const nextStatus = nextRescueStatus(rescue.status);
      if (!nextStatus) {
        setOperatorNotice(`${rescue.victim_name} is already marked rescued`);
        return;
      }
      const unit = rescue.assigned_unit || recommendedUnitForRescue(
        rescue,
        disaster,
        role,
        responseHub.responder_units || [],
        facilities.ambulances,
      );
      if (!unit) {
        setOperatorNotice('No verified responder or ambulance is available. Register a unit before assigning this rescue.');
        return;
      }
      try {
        const response = rescue.assigned_unit
          ? await api.updateRescue(id, { status: nextStatus, note: `${role} advanced the response` })
          : await api.assignRescue(id, { status: nextStatus, assigned_unit: unit });
        setRescues((items) => items.map((item) => (item.id === id ? response.rescue_request : item)));
        setOperatorNotice(`${rescue.victim_name} moved to ${nextStatus} with ${unit}`);
      } catch (error) {
        setOperatorNotice(`Rescue status was not changed: ${error.message}`);
        if (isNetworkFailure(error)) setConnectionState('offline');
      }
      return;
    }

    if (role === 'Ambulance') {
      const nextStatus = nextRescueStatus(rescue.status);
      if (!nextStatus) {
        setOperatorNotice(`${rescue.victim_name} is already marked rescued`);
        return;
      }
      try {
        const response = await api.updateRescue(id, {
          status: nextStatus,
          note: 'Assigned ambulance advanced the response',
        });
        setRescues((items) => items.map((item) => (item.id === id ? response.rescue_request : item)));
        setOperatorNotice(`${rescue.victim_name} moved to ${nextStatus} by the assigned ambulance`);
      } catch (error) {
        setOperatorNotice(`Rescue status was not changed: ${error.message}`);
        if (isNetworkFailure(error)) setConnectionState('offline');
      }
      return;
    }

    if (role === 'Hospital') {
      const nextStatus = rescue.status === 'rescued' ? rescue.status : 'triage';
      const assignedUnit = rescue.assigned_unit || (facilities.hospitals[0]?.name ? `${facilities.hospitals[0].name} triage desk` : '');
      if (!assignedUnit) {
        setOperatorNotice('No hospital is linked to this account. Ask an administrator to complete facility setup.');
        return;
      }
      try {
        const response = await api.updateRescue(id, { status: nextStatus, assigned_unit: assignedUnit, note: 'Accepted by hospital triage' });
        setRescues((items) => items.map((item) => (item.id === id ? response.rescue_request : item)));
        setOperatorNotice(`${rescue.victim_name} accepted for hospital triage`);
      } catch (error) {
        setOperatorNotice(`Hospital triage status was not changed: ${error.message}`);
        if (isNetworkFailure(error)) setConnectionState('offline');
      }
      return;
    }

    if (role === 'Volunteer') {
      const nextStatus = rescue.status === 'rescued' ? rescue.status : 'en route';
      const assignedUnit = rescue.assigned_unit || currentUserName;
      if (!assignedUnit) {
        setOperatorNotice('The volunteer account identity could not be loaded. Sign in again before checking in.');
        return;
      }
      try {
        const response = await api.updateRescue(id, { status: nextStatus, assigned_unit: assignedUnit, note: 'Volunteer check-in recorded' });
        setRescues((items) => items.map((item) => (item.id === id ? response.rescue_request : item)));
        setOperatorNotice(`Volunteer check-in recorded for ${rescue.victim_name}`);
      } catch (error) {
        setOperatorNotice(`Volunteer check-in was not recorded: ${error.message}`);
        if (isNetworkFailure(error)) setConnectionState('offline');
      }
      return;
    }

    setOperatorNotice(`Showing live tracking for ${rescue.victim_name}: ${rescue.status}`);
  }

  async function updateHospital(id, delta) {
    const hospital = facilities.hospitals.find((item) => item.id === id);
    if (hospital) {
      const availableBeds = clampNumber(hospital.available_beds + delta, 0, hospital.total_beds);
      try {
        const response = await api.updateHospital(id, { available_beds: availableBeds });
        setFacilities((current) => ({ ...current, hospitals: current.hospitals.map((item) => (item.id === id ? response.hospital : item)) }));
        setOperatorNotice(`${hospital.name} capacity ${delta > 0 ? 'increased' : 'reduced'} by ${Math.abs(delta)} beds`);
      } catch (error) {
        setOperatorNotice(`Hospital capacity was not changed: ${error.message}`);
        if (isNetworkFailure(error)) setConnectionState('offline');
      }
    }
  }

  async function updateShelter(id, delta) {
    const shelter = facilities.shelters.find((item) => item.id === id);
    if (shelter) {
      const availableCapacity = clampNumber(shelter.available_capacity + delta, 0, shelter.total_capacity);
      try {
        const response = await api.updateShelter(id, { available_capacity: availableCapacity });
        setFacilities((current) => ({ ...current, shelters: current.shelters.map((item) => (item.id === id ? response.shelter : item)) }));
        setOperatorNotice(`${shelter.name} slots ${delta > 0 ? 'opened' : 'filled'} by ${Math.abs(delta)}`);
      } catch (error) {
        setOperatorNotice(`Shelter capacity was not changed: ${error.message}`);
        if (isNetworkFailure(error)) setConnectionState('offline');
      }
    }
  }

  async function updateAmbulanceStatus(id) {
    const ambulance = facilities.ambulances.find((item) => item.id === id);
    if (!ambulance) return;
    const nextStatus = nextAmbulanceStatus(ambulance.status);
    try {
      const response = await api.updateAmbulance(id, { status: nextStatus });
      setFacilities((current) => ({ ...current, ambulances: current.ambulances.map((item) => (item.id === id ? response.ambulance : item)) }));
      setOperatorNotice(`${ambulance.vehicle_number} marked ${nextStatus}`);
    } catch (error) {
      setOperatorNotice(`Ambulance status was not changed: ${error.message}`);
      if (isNetworkFailure(error)) setConnectionState('offline');
    }
  }

  async function findSafeRoute(destination = 'shelter') {
    try {
      const result = await api.safeRoute({ latitude: rescueDraft.latitude, longitude: rescueDraft.longitude, destination });
      setRouteResult(result);
      setOperatorNotice(`Nearest available ${destination}: ${result.destination.name}, ${result.distance_km} km away`);
    } catch (error) {
      setRouteResult(null);
      setOperatorNotice(`Safe-route lookup failed: ${error.message}`);
    }
  }

  async function acknowledgeAlert(alert) {
    try {
      const response = await api.acknowledgeAlert(alert.id, { response: 'received', latitude: rescueDraft.latitude, longitude: rescueDraft.longitude });
      setAlerts((items) => items.map((item) => (item.id === alert.id ? { ...item, acknowledged: true, acknowledgement_count: Number(item.acknowledgement_count || 0) + (response.created ? 1 : 0) } : item)));
      setOperatorNotice(`Warning receipt confirmed for ${alert.audience}`);
    } catch (error) {
      setOperatorNotice(`Could not acknowledge warning: ${error.message}`);
    }
  }

  async function submitDistribution(event) {
    event.preventDefault();
    try {
      await api.createDistribution(distributionDraft);
      const coordination = await api.coordination();
      setCoordinationData(coordination);
      setResources(coordination.resources);
      alignOperationalDrafts({ disasters, resources: coordination.resources, response_hub: responseHub }, coordination);
      setOperatorNotice(`Relief inventory dispatched to ${distributionDraft.destination}`);
    } catch (error) {
      setOperatorNotice(`Distribution could not be planned: ${error.message}`);
    }
  }

  async function submitVolunteerAssignment(event) {
    event.preventDefault();
    try {
      await api.createVolunteerAssignment(volunteerDraft);
      const coordination = await api.coordination();
      setCoordinationData(coordination);
      alignOperationalDrafts({ disasters, resources, response_hub: responseHub }, coordination);
      setOperatorNotice('Volunteer assignment created and availability updated');
    } catch (error) {
      setOperatorNotice(`Volunteer could not be assigned: ${error.message}`);
    }
  }

  function captureDeviceLocation(target) {
    if (!navigator.geolocation) {
      setOperatorNotice('Device location is not supported by this browser; enter coordinates manually and call 112 if in immediate danger');
      return;
    }
    setOperatorNotice('Waiting for your device location permission...');
    navigator.geolocation.getCurrentPosition(
      async ({ coords }) => {
        const location = { latitude: Number(coords.latitude.toFixed(6)), longitude: Number(coords.longitude.toFixed(6)), location_accuracy: Math.round(coords.accuracy), location_consent: true };
        if (target === 'rescue') setRescueDraft((current) => ({ ...current, ...location }));
        if (target === 'supply') setSupplyDraft((current) => ({ ...current, ...location }));
        if (target === 'welfare') setWelfareDraft((current) => ({ ...current, latitude: location.latitude, longitude: location.longitude }));
        try {
          await api.shareLocation({ latitude: location.latitude, longitude: location.longitude, accuracy_meters: location.location_accuracy, consent_granted: true, source: 'device' });
          setOperatorNotice(`Location shared with responders to approximately ${location.location_accuracy} m accuracy`);
        } catch (error) {
          setOperatorNotice(`Location captured for this request; live sharing will retry on submission (${error.message})`);
        }
      },
      (error) => setOperatorNotice(`Location was not shared: ${error.message}. Enter coordinates manually or call 112.`),
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 },
    );
  }

  async function submitWelfareCheck(event) {
    event.preventDefault();
    try {
      const response = await api.createWelfareCheck(welfareDraft);
      setResponseHub((current) => ({ ...current, welfare_checks: [response.welfare_check, ...current.welfare_checks] }));
      setWelfareDraft((current) => ({ ...current, relative_name: '', relative_phone: '', relationship: '', last_known_location: '', consent_to_contact: false }));
      setOperatorNotice(`Welfare check opened for ${response.welfare_check.relative_name}; call responders can now update the case`);
    } catch (error) {
      setOperatorNotice(`Welfare check could not be opened: ${error.message}`);
    }
  }

  async function advanceWelfareCheck(item) {
    const statuses = ['requested', 'assigned', 'contacting', 'located_safe', 'closed'];
    const nextStatus = statuses[Math.min(statuses.length - 1, Math.max(0, statuses.indexOf(item.status)) + 1)];
    try {
      const response = await api.updateWelfareCheck(item.id, { status: nextStatus, responder_notes: `Responder updated case to ${nextStatus}` });
      setResponseHub((current) => ({ ...current, welfare_checks: current.welfare_checks.map((entry) => (entry.id === item.id ? response.welfare_check : entry)) }));
      setOperatorNotice(`${item.relative_name} welfare check updated to ${nextStatus}`);
    } catch (error) {
      setOperatorNotice(`Welfare check update failed: ${error.message}`);
    }
  }

  async function submitSupplyRequest(event) {
    event.preventDefault();
    try {
      const response = await api.createSupplyRequest(supplyDraft);
      setResponseHub((current) => ({ ...current, supply_requests: [response.supply_request, ...current.supply_requests] }));
      setSupplyDraft((current) => ({ ...current, description: '', location_consent: false }));
      setOperatorNotice(`Supply case #${response.supply_request.id} sent to nearby relief coordinators`);
    } catch (error) {
      setOperatorNotice(`Supply request could not be sent: ${error.message}`);
    }
  }

  async function advanceSupplyRequest(item, assignedUnit = '') {
    const statuses = ['requested', 'assigned', 'packing', 'en route', 'delivered'];
    const nextStatus = statuses[Math.min(statuses.length - 1, Math.max(0, statuses.indexOf(item.status)) + 1)];
    const unit = item.assigned_unit || assignedUnit;
    if (['assigned', 'packing', 'en route', 'delivered'].includes(nextStatus) && !unit) {
      setOperatorNotice('Select a registered available response unit before advancing this request.');
      return;
    }
    try {
      const response = await api.updateSupplyRequest(item.id, {
        status: nextStatus,
        ...(unit ? { assigned_unit: unit } : {}),
      });
      setResponseHub((current) => ({
        ...current,
        supply_requests: current.supply_requests.map((entry) => (entry.id === item.id ? response.supply_request : entry)),
        responder_units: response.responder_unit
          ? current.responder_units.map((entry) => (entry.id === response.responder_unit.id ? response.responder_unit : entry))
          : current.responder_units,
      }));
      setOperatorNotice(`Supply request #${item.id} moved to ${nextStatus}`);
    } catch (error) {
      setOperatorNotice(`Supply request update failed: ${error.message}`);
    }
  }

  async function acknowledgeHospitalPrep(item) {
    try {
      const response = await api.acknowledgeHospitalNotification(item.id);
      setResponseHub((current) => ({ ...current, hospital_notifications: current.hospital_notifications.map((entry) => (entry.id === item.id ? { ...entry, ...response.hospital_notification } : entry)) }));
      setOperatorNotice(`Hospital preparation notice #${item.id} acknowledged`);
    } catch (error) {
      setOperatorNotice(`Hospital acknowledgement failed: ${error.message}`);
    }
  }

  async function submitDonation(event) {
    event.preventDefault();
    try {
      const response = await api.createDonation(donationDraft);
      const amount = Number(response.donation.amount);
      setResponseHub((current) => ({
        ...current,
        campaigns: current.campaigns.map((campaign) => Number(campaign.id) === Number(response.donation.campaign_id) ? { ...campaign, pledged_amount: Number(campaign.pledged_amount || 0) + amount } : campaign),
      }));
      setDonationDraft((current) => ({ ...current, message: '' }));
      setOperatorNotice(`${response.message} Reference: ${response.donation.reference}`);
      if (response.checkout_url) window.open(response.checkout_url, '_blank', 'noopener,noreferrer');
    } catch (error) {
      setOperatorNotice(`Donation pledge failed: ${error.message}`);
    }
  }

  async function publishNewsUpdate(event) {
    event.preventDefault();
    try {
      const response = await api.createNewsUpdate(newsDraft);
      setResponseHub((current) => ({ ...current, news_updates: [response.news_update, ...current.news_updates] }));
      setNewsDraft((current) => ({ ...current, headline: '', summary: '', stream_url: '' }));
      setOperatorNotice('Verified disaster-area news update published');
    } catch (error) {
      setOperatorNotice(`News update could not be published: ${error.message}`);
    }
  }

  function alignOperationalDrafts(snapshot, coordination = null) {
    const firstDisasterId = snapshot.disasters?.[0]?.id;
    const firstResourceId = snapshot.resources?.[0]?.id;
    const firstCampaignId = snapshot.response_hub?.campaigns?.[0]?.id;
    const firstVolunteerId = coordination?.volunteers?.find((item) => item.availability_status === 'available')?.id;
    const keepDisasterId = (current) => (
      snapshot.disasters?.some((item) => Number(item.id) === Number(current)) ? current : firstDisasterId ?? ''
    );
    setRescueDraft((current) => ({ ...current, disaster_id: keepDisasterId(current.disaster_id) }));
    setWelfareDraft((current) => ({ ...current, disaster_id: keepDisasterId(current.disaster_id) }));
    setSupplyDraft((current) => ({ ...current, disaster_id: keepDisasterId(current.disaster_id) }));
    setNewsDraft((current) => ({ ...current, disaster_id: keepDisasterId(current.disaster_id) }));
    setDonationDraft((current) => ({
      ...current,
      campaign_id: snapshot.response_hub?.campaigns?.some((item) => Number(item.id) === Number(current.campaign_id))
        ? current.campaign_id
        : firstCampaignId ?? '',
    }));
    if (!coordination) return;
    setDistributionDraft((current) => ({
      ...current,
      disaster_id: keepDisasterId(current.disaster_id),
      resource_id: snapshot.resources?.some((item) => Number(item.id) === Number(current.resource_id)) ? current.resource_id : firstResourceId ?? '',
    }));
    setVolunteerDraft((current) => ({
      ...current,
      disaster_id: keepDisasterId(current.disaster_id),
      volunteer_id: coordination.volunteers?.some((item) => Number(item.id) === Number(current.volunteer_id) && item.availability_status === 'available')
        ? current.volunteer_id
        : firstVolunteerId ?? '',
    }));
  }

  function queueOfflineOperation(type, payload) {
    const next = [...readOfflineQueue(), { id: Date.now(), queued_at: Date.now(), type, payload }].slice(-OFFLINE_QUEUE_LIMIT);
    localStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(next));
    setPendingOperations(next);
  }

  async function flushOfflineQueue() {
    const queued = readOfflineQueue();
    if (!queued.length) return;
    const remaining = [];
    for (const operation of queued) {
      try {
        if (operation.type === 'disaster') await api.createDisaster(operation.payload);
        if (operation.type === 'rescue') await api.createRescue(operation.payload);
      } catch {
        remaining.push(operation);
      }
    }
    localStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(remaining));
    setPendingOperations(remaining);
    if (!remaining.length) setOperatorNotice(`${queued.length} offline submission${queued.length === 1 ? '' : 's'} synchronized`);
  }

  function cycleSortMode() {
    const currentIndex = sortModes.indexOf(sortMode);
    const nextMode = sortModes[(currentIndex + 1) % sortModes.length];
    setSortMode(nextMode);
    setOperatorNotice(sortLabels[nextMode]);
  }

  function clearOperationalFilters() {
    setSearchQuery('');
    setFilters({ type: 'all', severity: 'all', status: 'all' });
    setOperatorNotice('Showing all India operations');
  }

  async function submitAuthentication(event) {
    event.preventDefault();
    if (authMode === 'register' && authDraft.password !== authDraft.password_confirmation) {
      setOperatorNotice('Registration failed: password confirmation does not match');
      return;
    }
    try {
      const session = authMode === 'login'
        ? await login({ email: authDraft.email, password: authDraft.password })
        : await register(authDraft);
      if (session.mfa_required) {
        setMfaChallenge({ token: session.challenge_token, code: '' });
        setAuthDraft((current) => ({ ...current, password: '', password_confirmation: '' }));
        setOperatorNotice(session.message);
        return;
      }
      if (session.pending_verification) {
        setCurrentUser(null);
        setSessionMode('account');
        setAuthDraft((current) => ({ ...current, password: '', password_confirmation: '' }));
        setOperatorNotice(session.message);
        return;
      }
      setCurrentUser(session.user);
      setSessionMode('account');
      setActiveRole(session.user.role);
      setMfaSession({
        required: Boolean(session.user.mfa_required),
        enabled: Boolean(session.user.mfa_enabled),
        verified: Boolean(session.mfa_verified),
        setup_required: Boolean(session.mfa_setup_required),
        recovery_codes_remaining: 0,
      });
      setAuthDraft((current) => ({ ...current, password: '', password_confirmation: '' }));
      setMfaChallenge({ token: '', code: '' });
      const passwordRequired = Boolean(session.user.password_change_required);
      setShowAccountPanel(passwordRequired || Boolean(session.mfa_setup_required));
      setOperatorNotice(
        passwordRequired
          ? 'Password accepted. Replace the temporary password to continue.'
          : session.mfa_setup_required
            ? 'Set up multi-factor authentication to continue.'
            : `${session.user.name} signed in successfully`,
      );
    } catch (error) {
      setOperatorNotice(`${authMode === 'login' ? 'Sign in' : 'Registration'} failed: ${error.message}`);
    }
  }

  async function submitMfaChallenge(event) {
    event.preventDefault();
    try {
      const session = await completeMfaLogin({ challenge_token: mfaChallenge.token, code: mfaChallenge.code });
      setCurrentUser(session.user);
      setSessionMode('account');
      setActiveRole(session.user.role);
      setMfaSession({
        required: Boolean(session.user.mfa_required),
        enabled: true,
        verified: true,
        setup_required: false,
        recovery_codes_remaining: 0,
      });
      setMfaChallenge({ token: '', code: '' });
      setAuthDraft((current) => ({ ...current, password: '', password_confirmation: '' }));
      const passwordRequired = Boolean(session.user.password_change_required);
      setShowAccountPanel(passwordRequired);
      setOperatorNotice(
        passwordRequired
          ? 'Identity verified. Replace the temporary password to continue.'
          : `${session.user.name} signed in with multi-factor authentication`,
      );
    } catch (error) {
      setMfaChallenge((current) => ({ ...current, code: '' }));
      setOperatorNotice(`Verification failed: ${error.message}`);
    }
  }

  async function startMfaSetup(event) {
    event.preventDefault();
    try {
      const setup = await beginMfaSetup({ current_password: mfaSetup.current_password });
      setMfaSetup((current) => ({ ...current, ...setup, current_password: '', code: '', recovery_codes: [] }));
      setOperatorNotice('Authenticator secret created. Confirm the six-digit code to finish setup.');
    } catch (error) {
      setOperatorNotice(`MFA setup failed: ${error.message}`);
    }
  }

  async function confirmMfaEnrollment(event) {
    event.preventDefault();
    try {
      const result = await confirmMfaSetup({ code: mfaSetup.code });
      setMfaSetup((current) => ({ ...current, code: '', secret: '', provisioning_uri: '', recovery_codes: result.recovery_codes }));
      setMfaSession((current) => ({ ...current, enabled: true, verified: true, setup_required: false, recovery_codes_remaining: result.recovery_codes.length }));
      setShowAccountPanel(true);
      setOperatorNotice('Multi-factor authentication enabled. Save every recovery code now.');
    } catch (error) {
      setOperatorNotice(`MFA confirmation failed: ${error.message}`);
    }
  }

  async function regenerateRecoveryCodes() {
    try {
      const result = await regenerateMfaRecoveryCodes(mfaAction);
      setMfaSetup((current) => ({ ...current, recovery_codes: result.recovery_codes }));
      setMfaAction({ current_password: '', code: '' });
      setMfaSession((current) => ({ ...current, recovery_codes_remaining: result.recovery_codes.length }));
      setOperatorNotice('New recovery codes generated. Previous recovery codes no longer work.');
    } catch (error) {
      setOperatorNotice(`Recovery-code regeneration failed: ${error.message}`);
    }
  }

  async function turnOffMfa() {
    try {
      const result = await disableMfa(mfaAction);
      const setupRequired = Boolean(result.setup_required);
      setMfaAction({ current_password: '', code: '' });
      setMfaSetup({ current_password: '', code: '', secret: '', provisioning_uri: '', recovery_codes: [] });
      setMfaSession((current) => ({ ...current, enabled: false, verified: false, setup_required: setupRequired, recovery_codes_remaining: 0 }));
      setShowAccountPanel(true);
      setOperatorNotice(setupRequired ? 'MFA must be enrolled again before operational access resumes.' : 'Multi-factor authentication disabled.');
    } catch (error) {
      setOperatorNotice(`MFA disable failed: ${error.message}`);
    }
  }

  async function submitPasswordChange(event) {
    event.preventDefault();
    if (passwordDraft.new_password !== passwordDraft.new_password_confirmation) {
      setOperatorNotice('Password change failed: password confirmation does not match');
      return;
    }
    try {
      const response = await changePassword({
        current_password: passwordDraft.current_password,
        new_password: passwordDraft.new_password,
      });
      setCurrentUser(response.user);
      setPasswordDraft(emptyPasswordDraft);
      setMfaSession((current) => ({
        ...current,
        verified: Boolean(response.mfa_verified),
        setup_required: Boolean(response.mfa_setup_required),
      }));
      setShowAccountPanel(Boolean(response.mfa_setup_required));
      setOperatorNotice(
        response.mfa_setup_required
          ? 'Password changed and other sessions revoked. Set up multi-factor authentication to continue.'
          : 'Password changed and other sessions revoked',
      );
    } catch (error) {
      setOperatorNotice(`Password change failed: ${error.message}`);
    }
  }

  async function submitProvisionedUser(event) {
    event.preventDefault();
    if (provisionDraft.password !== provisionDraft.password_confirmation) {
      setOperatorNotice('User provisioning failed: password confirmation does not match');
      return;
    }
    try {
      const response = await api.provisionUser(provisionDraft);
      setManagedUsers((items) => [response.user, ...items]);
      if (response.facility && provisionDraft.facility_id === 'new') {
        const key = response.user.role === 'Hospital' ? 'hospitals' : response.user.role === 'Shelter' ? 'shelters' : 'ambulances';
        setFacilities((current) => ({ ...current, [key]: [...current[key], response.facility] }));
      }
      setProvisionDraft({ ...emptyProvisionDraft, facility: { ...emptyProvisionDraft.facility } });
      setOperatorNotice(
        `${response.user.name} provisioned as ${response.user.role}; they must replace the temporary password on first sign-in`,
      );
    } catch (error) {
      setOperatorNotice(`User provisioning failed: ${error.message}`);
    }
  }

  async function updateManagedUser(user, payload) {
    try {
      const response = await api.updateUserAccess(user.id, payload);
      setManagedUsers((items) => items.map((item) => (item.id === user.id ? response.user : item)));
      setOperatorNotice(`${response.user.name} access updated`);
    } catch (error) {
      setOperatorNotice(`Access update failed: ${error.message}`);
    }
  }

  async function submitPasswordReset(event) {
    event.preventDefault();
    if (resetDraft.new_password !== resetDraft.password_confirmation) {
      setOperatorNotice('Password reset failed: password confirmation does not match');
      return;
    }
    try {
      await api.resetUserPassword(resetDraft.user_id, resetDraft);
      setManagedUsers((items) => items.map((item) => (
        String(item.id) === String(resetDraft.user_id)
          ? { ...item, password_change_required: true }
          : item
      )));
      setResetDraft({ user_id: '', admin_password: '', new_password: '', password_confirmation: '' });
      setOperatorNotice('Password reset completed; the user must replace it at next sign-in and all sessions were revoked');
    } catch (error) {
      setOperatorNotice(`Password reset failed: ${error.message}`);
    }
  }

  async function submitMfaReset(event) {
    event.preventDefault();
    try {
      const response = await api.resetUserMfa(mfaResetDraft.user_id, mfaResetDraft);
      setManagedUsers((items) => items.map((item) => (
        String(item.id) === String(mfaResetDraft.user_id)
          ? response.user
          : item
      )));
      setMfaResetDraft({ user_id: '', admin_password: '' });
      setOperatorNotice(
        response.mfa_setup_required
          ? 'MFA reset completed; sessions were revoked and the user must enroll a new authenticator'
          : 'MFA reset completed and all active sessions were revoked',
      );
    } catch (error) {
      setOperatorNotice(`MFA reset failed: ${error.message}`);
    }
  }

  async function revokeAccountSession(session) {
    try {
      await revokeSession(session.id);
      if (session.current) {
        await signOut();
        return;
      }
      setAccountSessions((items) => items.filter((item) => item.id !== session.id));
      setOperatorNotice('The selected session was revoked');
    } catch (error) {
      setOperatorNotice(`Session could not be revoked: ${error.message}`);
    }
  }

  async function submitResource(event) {
    event.preventDefault();
    try {
      const response = await api.createResource(resourceDraft);
      setResources((items) => [...items, response.resource]);
      setResourceDraft({ name: '', category: 'food', unit: 'units', available_quantity: 0, storage_location: '' });
      setOperatorNotice(`${response.resource.name} added to the live resource inventory`);
    } catch (error) {
      setOperatorNotice(`Resource setup failed: ${error.message}`);
    }
  }

  async function submitResponder(event) {
    event.preventDefault();
    try {
      const response = await api.createResponder(responderDraft);
      setResponseHub((current) => ({
        ...current,
        responder_units: [...(current.responder_units || []), response.responder],
      }));
      setResponderDraft({ name: '', unit_type: 'professional rescue', skills: '', contact_phone: '', latitude: '', longitude: '' });
      setOperatorNotice(`${response.responder.name} added to automatic dispatch`);
    } catch (error) {
      setOperatorNotice(`Responder setup failed: ${error.message}`);
    }
  }

  async function submitCampaign(event) {
    event.preventDefault();
    try {
      const response = await api.createDonationCampaign(campaignDraft);
      setResponseHub((current) => ({
        ...current,
        campaigns: [response.campaign, ...(current.campaigns || [])],
      }));
      setDonationDraft((current) => ({ ...current, campaign_id: current.campaign_id || response.campaign.id }));
      setCampaignDraft({ disaster_id: '', title: '', description: '', goal_amount: '', currency: 'INR', organizer: '' });
      setOperatorNotice(`${response.campaign.title} opened for verified pledges`);
    } catch (error) {
      setOperatorNotice(`Campaign setup failed: ${error.message}`);
    }
  }

  async function signOut() {
    try {
      await logout();
    } catch {
      // Local state is still cleared when the server session has expired.
    }
    localStorage.removeItem(OFFLINE_QUEUE_KEY);
    setPendingOperations([]);
    setCurrentUser(null);
    setAuthDraft(emptyAuthDraft);
    setPasswordDraft(emptyPasswordDraft);
    setMfaChallenge({ token: '', code: '' });
    setMfaSession({ required: false, enabled: false, verified: false, setup_required: false, recovery_codes_remaining: 0 });
    setMfaSetup({ current_password: '', code: '', secret: '', provisioning_uri: '', recovery_codes: [] });
    setMfaAction({ current_password: '', code: '' });
    setAccountSessions([]);
    setProvisionDraft({ ...emptyProvisionDraft, facility: { ...emptyProvisionDraft.facility } });
    setResetDraft({ user_id: '', admin_password: '', new_password: '', password_confirmation: '' });
    setMfaResetDraft({ user_id: '', admin_password: '' });
    setSessionMode(DEMO_ENABLED ? 'demo' : 'account');
    setShowAccountPanel(!DEMO_ENABLED);
    setActiveRole('Citizen');
    setOperatorNotice('Signed out successfully');
  }

  if (!DEMO_ENABLED && (!currentUser || passwordChangeRequired || mfaSession.setup_required)) {
    return (
      <main className="auth-gate">
        <div className="auth-gate-brand">
          <div className="brand-mark"><ShieldAlert size={28} /></div>
          <div><strong>ResQ Command</strong><span>Secure disaster response workspace</span></div>
        </div>
        {sessionMode === 'checking' ? (
          <section className="panel auth-gate-loading"><RefreshCw size={22} /><h1>Restoring your secure session</h1></section>
        ) : (
          <AccountPanel
            mode={authMode}
            setMode={setAuthMode}
            draft={authDraft}
            setDraft={setAuthDraft}
            onSubmit={submitAuthentication}
            currentUser={currentUser}
            sessionMode={sessionMode}
            demoEnabled={false}
            notice={operatorNotice}
            passwordDraft={passwordDraft}
            setPasswordDraft={setPasswordDraft}
            onPasswordChange={submitPasswordChange}
            mfaChallenge={mfaChallenge}
            setMfaChallenge={setMfaChallenge}
            onMfaChallenge={submitMfaChallenge}
            mfaSession={mfaSession}
            mfaSetup={mfaSetup}
            setMfaSetup={setMfaSetup}
            onMfaSetup={startMfaSetup}
            onMfaConfirm={confirmMfaEnrollment}
            mfaAction={mfaAction}
            setMfaAction={setMfaAction}
            onRecoveryRegenerate={regenerateRecoveryCodes}
            onMfaDisable={turnOffMfa}
            sessions={accountSessions}
            onSessionRevoke={revokeAccountSession}
            onLogout={signOut}
          />
        )}
      </main>
    );
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
        <select
          id="role-select"
          className="form-select"
          value={activeRole}
          disabled={sessionMode === 'account'}
          onChange={(event) => {
            if (!DEMO_ENABLED) return;
            setSessionMode('demo');
            setActiveRole(event.target.value);
            setActiveView('command');
            setOperatorNotice(`${event.target.value} role selected`);
          }}
        >
          {roles.map((role) => (
            <option key={role}>{role}</option>
          ))}
        </select>

        <nav className="nav-stack" aria-label="Main views">
          {activeNavigation.map(({ id, label, icon: Icon }) => (
            <button key={id} className={visibleActiveView === id ? 'active' : ''} onClick={() => setActiveView(id)}>
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
            <input
              aria-label="Search operations"
              placeholder="Search incident, state, shelter, patient..."
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
            />
          </div>
          <div className="topbar-tools">
            <button
              type="button"
              className={`sync-state sync-${connectionState}`}
              onClick={() => flushOfflineQueue()}
              title={currentUser ? `Authenticated as ${currentUser.name}` : 'Using local fallback data'}
            >
              {connectionState === 'online' ? <Wifi size={16} /> : connectionState === 'connecting' ? <RefreshCw size={16} /> : <CloudOff size={16} />}
              {connectionState === 'online' ? 'Live API' : connectionState === 'connecting' ? 'Connecting' : 'Offline'}
              {pendingOperations.length ? ` · ${pendingOperations.length} queued` : ''}
            </button>
            <button type="button" onClick={cycleSortMode}>
              <ArrowUpDown size={16} />
              {sortLabels[sortMode]}
            </button>
            <button type="button" className={showFilters ? 'active' : ''} onClick={() => setShowFilters((value) => !value)}>
              <SlidersHorizontal size={16} />
              Filters{activeFilterCount ? ` (${activeFilterCount})` : ''}
            </button>
            <button
              type="button"
              onClick={() => {
                setShowAccountPanel((value) => !value);
              }}
            >
              <UserRound size={16} />
              {sessionMode === 'account' ? currentUser?.name || activeRole : `${activeRole} demo`}
            </button>
            <button
              type="button"
              className="primary-action"
              onClick={() => {
                setActiveView(activeTopbar.view);
                setOperatorNotice(`${activeTopbar.action} opened`);
              }}
            >
              <Plus size={17} />
              {activeTopbar.action}
            </button>
          </div>
        </header>

        {showAccountPanel && (
          <AccountPanel
            mode={authMode}
            setMode={setAuthMode}
            draft={authDraft}
            setDraft={setAuthDraft}
            onSubmit={submitAuthentication}
            currentUser={currentUser}
            sessionMode={sessionMode}
            demoEnabled={DEMO_ENABLED}
            notice={operatorNotice}
            passwordDraft={passwordDraft}
            setPasswordDraft={setPasswordDraft}
            onPasswordChange={submitPasswordChange}
            mfaChallenge={mfaChallenge}
            setMfaChallenge={setMfaChallenge}
            onMfaChallenge={submitMfaChallenge}
            mfaSession={mfaSession}
            mfaSetup={mfaSetup}
            setMfaSetup={setMfaSetup}
            onMfaSetup={startMfaSetup}
            onMfaConfirm={confirmMfaEnrollment}
            mfaAction={mfaAction}
            setMfaAction={setMfaAction}
            onRecoveryRegenerate={regenerateRecoveryCodes}
            onMfaDisable={turnOffMfa}
            sessions={accountSessions}
            onSessionRevoke={revokeAccountSession}
            onLogout={signOut}
            onReturnToDemo={() => {
              setSessionMode('demo');
              setShowAccountPanel(false);
              setOperatorNotice(`${activeRole} demo session restored`);
            }}
          />
        )}

        {showFilters && (
          <section className="filter-panel" aria-label="Operational filters">
            <Select
              label="Disaster type"
              value={filters.type}
              options={[{ label: 'All types', value: 'all' }, ...disasterOptions.map((type) => ({ label: type, value: type }))]}
              onChange={(value) => setFilters((current) => ({ ...current, type: value }))}
            />
            <Select
              label="Risk level"
              value={filters.severity}
              options={[{ label: 'All levels', value: 'all' }, ...severityOptions.map((level) => ({ label: level, value: level }))]}
              onChange={(value) => setFilters((current) => ({ ...current, severity: value }))}
            />
            <Select
              label="Status"
              value={filters.status}
              options={[{ label: 'All statuses', value: 'all' }, ...filterStatusOptions.map((status) => ({ label: status, value: status }))]}
              onChange={(value) => setFilters((current) => ({ ...current, status: value }))}
            />
            <button type="button" className="compact-button secondary-button" onClick={clearOperationalFilters}>
              Clear
            </button>
          </section>
        )}

        <section className="page-heading">
          <div>
            <p>{activeTopbar.eyebrow}</p>
            <h1>{activeTopbar.title}</h1>
            <span className="operator-notice">{operatorNotice} - {filterSummary}</span>
          </div>
          <StatusPill value={activeRole} />
        </section>

        <AnimatePresence mode="wait">
          {visibleActiveView === 'command' && (
            <MotionPage key="command" reduceMotion={reduceMotion}>
              {activeRole === 'Admin' ? (
                <CommandView
                  metrics={metrics}
                  disasters={filteredDisasters}
                  rescues={sortedRescues}
                  facilities={facilities}
                  resources={resources}
                  readinessPillars={readinessPillars}
                  fieldTeams={responseHub.responder_units || []}
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
                  filterSummary={filterSummary}
                />
              ) : (
                <RoleDashboard
                  role={activeRole}
                  metrics={metrics}
                  disasters={filteredDisasters}
                  rescues={visibleRescues}
                  facilities={facilities}
                  alerts={alerts}
                  resources={resources}
                  responseHub={responseHub}
                  coordination={coordinationData}
                  setActiveView={setActiveView}
                  onAcknowledge={acknowledgeAlert}
                />
              )}
            </MotionPage>
          )}
          {visibleActiveView === 'report' && (
            <MotionPage key="report" reduceMotion={reduceMotion}>
              <ReportView
                draft={incidentDraft}
                setDraft={setIncidentDraft}
                onSubmit={submitIncident}
                rescueDraft={rescueDraft}
                setRescueDraft={setRescueDraft}
                disasters={disasters}
                onRescueSubmit={submitRescue}
                routeResult={routeResult}
                onFindSafeRoute={findSafeRoute}
                onUseDeviceLocation={() => captureDeviceLocation('rescue')}
              />
            </MotionPage>
          )}
          {visibleActiveView === 'rescue' && (
            <MotionPage key="rescue" reduceMotion={reduceMotion}>
              <RescueView
                role={activeRole}
                rescues={visibleRescues}
                disasters={disasters}
                selectedRescueId={selectedRescueId}
                onAction={handleRescueAction}
                onSelect={setSelectedRescueId}
              />
            </MotionPage>
          )}
          {visibleActiveView === 'facilities' && (
            <MotionPage key="facilities" reduceMotion={reduceMotion}>
              <FacilitiesView
                role={activeRole}
                facilities={facilities}
                updateHospital={updateHospital}
                updateShelter={updateShelter}
                updateAmbulanceStatus={updateAmbulanceStatus}
              />
            </MotionPage>
          )}
          {visibleActiveView === 'coordination' && (
            <MotionPage key="coordination" reduceMotion={reduceMotion}>
              <CoordinationView
                disasters={disasters}
                resources={resources}
                coordination={coordinationData}
                distributionDraft={distributionDraft}
                setDistributionDraft={setDistributionDraft}
                volunteerDraft={volunteerDraft}
                setVolunteerDraft={setVolunteerDraft}
                onDistributionSubmit={submitDistribution}
                onVolunteerSubmit={submitVolunteerAssignment}
              />
            </MotionPage>
          )}
          {visibleActiveView === 'access' && activeRole === 'Admin' && (
            <MotionPage key="access" reduceMotion={reduceMotion}>
              <UserAccessView
                users={managedUsers}
                currentUser={currentUser}
                provisionDraft={provisionDraft}
                setProvisionDraft={setProvisionDraft}
                onProvision={submitProvisionedUser}
                onUpdate={updateManagedUser}
                resetDraft={resetDraft}
                setResetDraft={setResetDraft}
                onResetPassword={submitPasswordReset}
                mfaResetDraft={mfaResetDraft}
                setMfaResetDraft={setMfaResetDraft}
                onResetMfa={submitMfaReset}
                facilities={facilities}
              />
            </MotionPage>
          )}
          {visibleActiveView === 'setup' && activeRole === 'Admin' && (
            <MotionPage key="setup" reduceMotion={reduceMotion}>
              <OperationalSetupView
                disasters={disasters}
                resourceDraft={resourceDraft}
                setResourceDraft={setResourceDraft}
                onResourceSubmit={submitResource}
                responderDraft={responderDraft}
                setResponderDraft={setResponderDraft}
                onResponderSubmit={submitResponder}
                campaignDraft={campaignDraft}
                setCampaignDraft={setCampaignDraft}
                onCampaignSubmit={submitCampaign}
              />
            </MotionPage>
          )}
          {visibleActiveView === 'response-hub' && (
            <MotionPage key="response-hub" reduceMotion={reduceMotion}>
              <ResponseHubView
                role={activeRole}
                disasters={disasters}
                alerts={alerts}
                hub={responseHub}
                welfareDraft={welfareDraft}
                setWelfareDraft={setWelfareDraft}
                supplyDraft={supplyDraft}
                setSupplyDraft={setSupplyDraft}
                donationDraft={donationDraft}
                setDonationDraft={setDonationDraft}
                newsDraft={newsDraft}
                setNewsDraft={setNewsDraft}
                onWelfareSubmit={submitWelfareCheck}
                onWelfareAdvance={advanceWelfareCheck}
                onSupplySubmit={submitSupplyRequest}
                onSupplyAdvance={advanceSupplyRequest}
                onHospitalAcknowledge={acknowledgeHospitalPrep}
                onDonationSubmit={submitDonation}
                onNewsSubmit={publishNewsUpdate}
                onUseDeviceLocation={captureDeviceLocation}
              />
            </MotionPage>
          )}
        </AnimatePresence>
      </section>
    </main>
  );
}

function AccountPanel({
  mode,
  setMode,
  draft,
  setDraft,
  onSubmit,
  currentUser,
  sessionMode,
  demoEnabled,
  notice,
  passwordDraft,
  setPasswordDraft,
  onPasswordChange,
  onLogout,
  onReturnToDemo,
  mfaChallenge,
  setMfaChallenge,
  onMfaChallenge,
  mfaSession,
  mfaSetup,
  setMfaSetup,
  onMfaSetup,
  onMfaConfirm,
  mfaAction,
  setMfaAction,
  onRecoveryRegenerate,
  onMfaDisable,
  sessions,
  onSessionRevoke,
}) {
  const hasAccountSession = sessionMode === 'account' && Boolean(currentUser);
  const awaitingMfa = Boolean(mfaChallenge?.token);
  const passwordChangeRequired = Boolean(currentUser?.password_change_required);
  return (
    <section className="panel account-panel" aria-label="Account access">
      <div>
        <p className="eyebrow">Authenticated access</p>
        <h2>{hasAccountSession ? 'Your operational account' : mode === 'login' ? 'Sign in to your operational account' : 'Create a citizen or volunteer account'}</h2>
        <span>
          {hasAccountSession
            ? `Signed in as ${currentUser?.name} (${currentUser?.role})`
            : demoEnabled
              ? 'Role switching remains available as a clearly marked local demo.'
              : 'Use your authorized account. Operational roles are provisioned by an administrator.'}
        </span>
      </div>
      {!hasAccountSession && notice && <p className="account-notice" role="status">{notice}</p>}
      {!hasAccountSession && !awaitingMfa && (
        <form className="account-form" onSubmit={onSubmit}>
          {mode === 'register' && (
            <>
              <Input label="Full name" value={draft.name} onChange={(value) => setDraft({ ...draft, name: value })} required autoComplete="name" />
              <Input label="Phone" value={draft.phone} onChange={(value) => setDraft({ ...draft, phone: value })} required autoComplete="tel" />
              <Select label="Account role" value={draft.role} options={['Citizen', 'Volunteer']} onChange={(value) => setDraft({ ...draft, role: value })} />
            </>
          )}
          <Input label="Email" type="email" value={draft.email} onChange={(value) => setDraft({ ...draft, email: value })} required autoComplete="email" />
          <Input label="Password (15+ characters)" type="password" value={draft.password} onChange={(value) => setDraft({ ...draft, password: value })} required minLength={15} autoComplete={mode === 'login' ? 'current-password' : 'new-password'} />
          {mode === 'register' && (
            <Input label="Confirm password" type="password" value={draft.password_confirmation} onChange={(value) => setDraft({ ...draft, password_confirmation: value })} required minLength={15} autoComplete="new-password" />
          )}
          <button className="primary-action" type="submit">
            <UserRound size={18} /> {mode === 'login' ? 'Sign in' : 'Create account'}
          </button>
          {mode === 'login' && (
            <p className="muted-copy">Forgot your password? Ask your organization’s ResQ administrator to verify your identity and issue a temporary replacement.</p>
          )}
        </form>
      )}
      {!hasAccountSession && awaitingMfa && (
        <form className="account-form" onSubmit={onMfaChallenge}>
          <p className="muted-copy">Your password was accepted. Enter the current six-digit authenticator code or one unused recovery code.</p>
          <Input
            label="Verification code"
            value={mfaChallenge.code}
            onChange={(value) => setMfaChallenge({ ...mfaChallenge, code: value })}
            required
            autoComplete="one-time-code"
          />
          <button className="primary-action" type="submit"><ShieldAlert size={18} /> Verify and sign in</button>
          <button type="button" className="compact-button secondary-button" onClick={() => setMfaChallenge({ token: '', code: '' })}>Use a different account</button>
        </form>
      )}
      {hasAccountSession && !passwordChangeRequired && mfaSetup.recovery_codes.length > 0 && (
        <section className="mfa-recovery-panel" aria-live="polite">
          <strong>Save these one-time recovery codes now</strong>
          <p className="muted-copy">Each code works once. Store them offline; they will not be shown again after this panel closes.</p>
          <div className="recovery-code-grid">
            {mfaSetup.recovery_codes.map((code) => <code key={code}>{code}</code>)}
          </div>
        </section>
      )}
      {hasAccountSession && !passwordChangeRequired && !mfaSession.enabled && !mfaSetup.secret && (
        <form className="account-form" onSubmit={onMfaSetup}>
          <strong>{mfaSession.required ? 'Multi-factor authentication is required' : 'Add multi-factor authentication'}</strong>
          <p className="muted-copy">Use any RFC 6238-compatible authenticator app. Re-enter your password to create a private setup key.</p>
          <Input label="Current password" type="password" value={mfaSetup.current_password} onChange={(value) => setMfaSetup({ ...mfaSetup, current_password: value })} required autoComplete="current-password" />
          <button className="primary-action" type="submit"><ShieldAlert size={18} /> Start authenticator setup</button>
        </form>
      )}
      {hasAccountSession && !passwordChangeRequired && !mfaSession.enabled && mfaSetup.secret && (
        <form className="account-form" onSubmit={onMfaConfirm}>
          <strong>Connect your authenticator</strong>
          <p className="muted-copy">Open the setup link on this device or enter the manual key in your authenticator. Then confirm a current code.</p>
          <a className="compact-button secondary-button" href={mfaSetup.provisioning_uri}>Open in authenticator app</a>
          <div className="mfa-secret"><span>Manual setup key</span><code>{mfaSetup.secret}</code></div>
          <Input label="Six-digit code" value={mfaSetup.code} onChange={(value) => setMfaSetup({ ...mfaSetup, code: value })} required autoComplete="one-time-code" inputMode="numeric" />
          <button className="primary-action" type="submit">Confirm and enable MFA</button>
        </form>
      )}
      {hasAccountSession && !passwordChangeRequired && mfaSession.enabled && (
        <section className="account-form">
          <strong>Multi-factor authentication is active</strong>
          <p className="muted-copy">{mfaSession.recovery_codes_remaining} recovery codes remain. Re-enter your password and a current authenticator or recovery code for either action below.</p>
          <Input label="Current password" type="password" value={mfaAction.current_password} onChange={(value) => setMfaAction({ ...mfaAction, current_password: value })} autoComplete="current-password" />
          <Input label="Verification code" value={mfaAction.code} onChange={(value) => setMfaAction({ ...mfaAction, code: value })} autoComplete="one-time-code" />
          <div className="account-actions">
            <button type="button" className="compact-button secondary-button" onClick={onRecoveryRegenerate}>Replace recovery codes</button>
            <button type="button" className="compact-button secondary-button" onClick={onMfaDisable}>Disable MFA</button>
          </div>
        </section>
      )}
      {hasAccountSession && (passwordChangeRequired || !mfaSession.setup_required) && (
        <form className="account-form" onSubmit={onPasswordChange}>
          <strong>{passwordChangeRequired ? 'Replace your temporary password' : 'Change password'}</strong>
          {passwordChangeRequired && (
            <p className="muted-copy">Choose a private password that was not supplied by an administrator. Operational access remains locked until this is complete.</p>
          )}
          <Input label="Current password" type="password" value={passwordDraft.current_password} onChange={(value) => setPasswordDraft({ ...passwordDraft, current_password: value })} required autoComplete="current-password" />
          <Input label="New password (15+ characters)" type="password" value={passwordDraft.new_password} onChange={(value) => setPasswordDraft({ ...passwordDraft, new_password: value })} required minLength={15} autoComplete="new-password" />
          <Input label="Confirm new password" type="password" value={passwordDraft.new_password_confirmation} onChange={(value) => setPasswordDraft({ ...passwordDraft, new_password_confirmation: value })} required minLength={15} autoComplete="new-password" />
          <button className="primary-action" type="submit">Change password</button>
        </form>
      )}
      {hasAccountSession && !passwordChangeRequired && !mfaSession.setup_required && sessions?.length > 0 && (
        <section className="account-form">
          <strong>Active sessions</strong>
          <p className="muted-copy">Revoke devices you no longer recognize. Revoking this device signs you out immediately.</p>
          <div className="managed-user-list">
            {sessions.map((session) => (
              <article className="managed-user" key={session.id}>
                <div>
                  <strong>{session.current ? 'This device' : 'Signed-in device'}</strong>
                  <span>{session.user_agent || 'Unknown browser'} · last used {formatDateTime(session.last_seen_at)}</span>
                </div>
                <button type="button" className="compact-button secondary-button" onClick={() => onSessionRevoke(session)}>
                  {session.current ? 'Sign out this device' : 'Revoke'}
                </button>
              </article>
            ))}
          </div>
        </section>
      )}
      <div className="account-actions">
        {!hasAccountSession && !awaitingMfa && (
          <button type="button" className="compact-button secondary-button" onClick={() => setMode(mode === 'login' ? 'register' : 'login')}>
            {mode === 'login' ? 'Create an account' : 'I already have an account'}
          </button>
        )}
        {hasAccountSession && onLogout && (
          <button type="button" className="compact-button secondary-button" onClick={onLogout}>Sign out</button>
        )}
        {demoEnabled && sessionMode === 'account' && (
          <button type="button" className="compact-button secondary-button" onClick={onReturnToDemo}>Return to demo mode</button>
        )}
      </div>
    </section>
  );
}

function UserAccessView({
  users,
  currentUser,
  provisionDraft,
  setProvisionDraft,
  onProvision,
  onUpdate,
  resetDraft,
  setResetDraft,
  onResetPassword,
  mfaResetDraft,
  setMfaResetDraft,
  onResetMfa,
  facilities,
}) {
  const resetCandidates = users
    .filter((user) => user.id !== currentUser?.id)
    .map((user) => ({ label: `${user.name} (${user.role})`, value: String(user.id) }));
  const facilityType = provisionDraft.role === 'Hospital'
    ? 'hospitals'
    : provisionDraft.role === 'Shelter'
      ? 'shelters'
      : provisionDraft.role === 'Ambulance'
        ? 'ambulances'
        : null;
  const facilityItems = facilityType ? facilities[facilityType] || [] : [];
  const facilityOptions = [
    { label: `Create a new ${provisionDraft.role.toLowerCase()} record`, value: 'new' },
    ...facilityItems.map((item) => ({
      label: item.name || item.vehicle_number,
      value: String(item.id),
    })),
  ];
  const updateFacility = (field, value) => setProvisionDraft({
    ...provisionDraft,
    facility: { ...provisionDraft.facility, [field]: value },
  });
  return (
    <div className="access-layout">
      <section className="panel">
        <PanelTitle eyebrow="Administrator control" title="Provision an operational account" />
        <p className="muted-copy">Create verified accounts for agencies, facilities, field teams, and additional administrators. Every administrator-supplied password must be replaced by its user before operational access unlocks.</p>
        <form className="access-form" onSubmit={onProvision}>
          <Input label="Full name" value={provisionDraft.name} onChange={(value) => setProvisionDraft({ ...provisionDraft, name: value })} required autoComplete="off" />
          <Input label="Email" type="email" value={provisionDraft.email} onChange={(value) => setProvisionDraft({ ...provisionDraft, email: value })} required autoComplete="off" />
          <Input label="Phone" value={provisionDraft.phone} onChange={(value) => setProvisionDraft({ ...provisionDraft, phone: value })} required autoComplete="off" />
          <Select
            label="Role"
            value={provisionDraft.role}
            options={roles}
            onChange={(value) => setProvisionDraft({ ...provisionDraft, role: value, facility_id: 'new' })}
          />
          <Input label="Organization" value={provisionDraft.organization_name} onChange={(value) => setProvisionDraft({ ...provisionDraft, organization_name: value })} autoComplete="off" />
          {facilityType && (
            <>
              <Select
                label={`${provisionDraft.role} assignment`}
                value={provisionDraft.facility_id}
                options={facilityOptions}
                onChange={(value) => setProvisionDraft({ ...provisionDraft, facility_id: value })}
              />
              {provisionDraft.facility_id === 'new' && (
                <div className="account-form">
                  {provisionDraft.role !== 'Ambulance' && (
                    <>
                      <Input label={`${provisionDraft.role} name`} value={provisionDraft.facility.name} onChange={(value) => updateFacility('name', value)} required />
                      <Input label="Address" value={provisionDraft.facility.address} onChange={(value) => updateFacility('address', value)} required />
                    </>
                  )}
                  {provisionDraft.role === 'Ambulance' && (
                    <>
                      <Input label="Vehicle number" value={provisionDraft.facility.vehicle_number} onChange={(value) => updateFacility('vehicle_number', value)} required />
                      <Input label="Driver name" value={provisionDraft.facility.driver_name} onChange={(value) => updateFacility('driver_name', value)} required />
                    </>
                  )}
                  <Input label="Facility contact phone" value={provisionDraft.facility.contact_phone} onChange={(value) => updateFacility('contact_phone', value)} required />
                  <Input label="Latitude" type="number" step="any" value={provisionDraft.facility.latitude} onChange={(value) => updateFacility('latitude', value)} required />
                  <Input label="Longitude" type="number" step="any" value={provisionDraft.facility.longitude} onChange={(value) => updateFacility('longitude', value)} required />
                  {provisionDraft.role === 'Hospital' && (
                    <>
                      <Input label="Total beds" type="number" value={provisionDraft.facility.total_beds} onChange={(value) => updateFacility('total_beds', value)} required />
                      <Input label="Available beds" type="number" value={provisionDraft.facility.available_beds} onChange={(value) => updateFacility('available_beds', value)} required />
                      <Input label="ICU beds" type="number" value={provisionDraft.facility.icu_beds} onChange={(value) => updateFacility('icu_beds', value)} required />
                      <Input label="Emergency capacity" type="number" value={provisionDraft.facility.emergency_capacity} onChange={(value) => updateFacility('emergency_capacity', value)} required />
                    </>
                  )}
                  {provisionDraft.role === 'Shelter' && (
                    <>
                      <Input label="Total capacity" type="number" value={provisionDraft.facility.total_capacity} onChange={(value) => updateFacility('total_capacity', value)} required />
                      <Input label="Available capacity" type="number" value={provisionDraft.facility.available_capacity} onChange={(value) => updateFacility('available_capacity', value)} required />
                      <label className="check-row">
                        <input type="checkbox" checked={provisionDraft.facility.food_available} onChange={(event) => updateFacility('food_available', event.target.checked)} />
                        Food available
                      </label>
                      <label className="check-row">
                        <input type="checkbox" checked={provisionDraft.facility.medical_support} onChange={(event) => updateFacility('medical_support', event.target.checked)} />
                        Medical support
                      </label>
                    </>
                  )}
                </div>
              )}
            </>
          )}
          <Input label="Initial password (15+ characters)" type="password" value={provisionDraft.password} onChange={(value) => setProvisionDraft({ ...provisionDraft, password: value })} required minLength={15} autoComplete="new-password" />
          <Input label="Confirm initial password" type="password" value={provisionDraft.password_confirmation} onChange={(value) => setProvisionDraft({ ...provisionDraft, password_confirmation: value })} required minLength={15} autoComplete="new-password" />
          <button className="primary-action" type="submit"><UserRound size={17} /> Provision verified user</button>
        </form>
      </section>

      <section className="panel">
        <PanelTitle eyebrow="Credential recovery" title="Reset another user’s access" />
        <p className="muted-copy">Re-enter your administrator password. A reset revokes every active session and forces the selected user to replace the temporary password at next sign-in.</p>
        <form className="access-form" onSubmit={onResetPassword}>
          <Select
            label="User"
            value={resetDraft.user_id}
            options={[{ label: 'Select a user', value: '' }, ...resetCandidates]}
            onChange={(value) => setResetDraft({ ...resetDraft, user_id: value })}
          />
          <Input label="Your administrator password" type="password" value={resetDraft.admin_password} onChange={(value) => setResetDraft({ ...resetDraft, admin_password: value })} required autoComplete="current-password" />
          <Input label="New password (15+ characters)" type="password" value={resetDraft.new_password} onChange={(value) => setResetDraft({ ...resetDraft, new_password: value })} required minLength={15} autoComplete="new-password" />
          <Input label="Confirm new password" type="password" value={resetDraft.password_confirmation} onChange={(value) => setResetDraft({ ...resetDraft, password_confirmation: value })} required minLength={15} autoComplete="new-password" />
          <button className="primary-action" type="submit" disabled={!resetDraft.user_id}>Reset password</button>
        </form>
        <div className="account-divider" />
        <p className="muted-copy">If a user has lost every authenticator and recovery code, remove the enrolled factor. All sessions are revoked, and roles that require MFA must enroll a new authenticator before operational access resumes.</p>
        <form className="access-form" onSubmit={onResetMfa}>
          <Select
            label="User with lost MFA"
            value={mfaResetDraft.user_id}
            options={[{ label: 'Select a user', value: '' }, ...resetCandidates]}
            onChange={(value) => setMfaResetDraft({ ...mfaResetDraft, user_id: value })}
          />
          <Input label="Your administrator password" type="password" value={mfaResetDraft.admin_password} onChange={(value) => setMfaResetDraft({ ...mfaResetDraft, admin_password: value })} required autoComplete="current-password" />
          <button className="primary-action" type="submit" disabled={!mfaResetDraft.user_id}>Reset MFA</button>
        </form>
      </section>

      <section className="panel access-users-panel">
        <PanelTitle eyebrow="Access directory" title={`${users.length} managed account${users.length === 1 ? '' : 's'}`} />
        <div className="managed-user-list">
          {users.map((user) => (
            <article className="managed-user" key={user.id}>
              <div>
                <strong>{user.name}</strong>
                <span>{user.email} · {user.role}{user.organization_name ? ` · ${user.organization_name}` : ''}</span>
                {user.password_change_required && <span>Temporary password must be replaced</span>}
                {user.mfa_required && <span>{user.mfa_enabled ? 'MFA enrolled' : 'MFA enrollment required'}</span>}
              </div>
              <StatusPill value={user.is_active ? user.verification_status : 'inactive'} />
              <div className="managed-user-actions">
                {user.verification_status === 'pending' && (
                  <>
                    <button type="button" className="compact-button" onClick={() => onUpdate(user, { verification_status: 'verified' })}>Verify</button>
                    <button type="button" className="compact-button secondary-button" onClick={() => onUpdate(user, { verification_status: 'rejected' })}>Reject</button>
                  </>
                )}
                {user.id !== currentUser?.id && user.verification_status !== 'pending' && (
                  <button type="button" className="compact-button secondary-button" onClick={() => onUpdate(user, { is_active: !user.is_active })}>
                    {user.is_active ? 'Deactivate' : 'Reactivate'}
                  </button>
                )}
              </div>
            </article>
          ))}
          {!users.length && <p className="muted-copy">No accounts have been provisioned yet.</p>}
        </div>
      </section>
    </div>
  );
}

function OperationalSetupView({
  disasters,
  resourceDraft,
  setResourceDraft,
  onResourceSubmit,
  responderDraft,
  setResponderDraft,
  onResponderSubmit,
  campaignDraft,
  setCampaignDraft,
  onCampaignSubmit,
}) {
  const disasterOptions = [
    { label: 'National / not tied to one incident', value: '' },
    ...disasters.map((item) => ({ label: item.title, value: String(item.id) })),
  ];
  return (
    <div className="access-layout">
      <section className="panel">
        <PanelTitle eyebrow="Logistics baseline" title="Add resource inventory" />
        <p className="muted-copy">Resources become available to NGO and administrator distribution planning immediately.</p>
        <form className="access-form" onSubmit={onResourceSubmit}>
          <Input label="Resource name" value={resourceDraft.name} onChange={(value) => setResourceDraft({ ...resourceDraft, name: value })} required />
          <Input label="Category" value={resourceDraft.category} onChange={(value) => setResourceDraft({ ...resourceDraft, category: value })} required />
          <Input label="Unit" value={resourceDraft.unit} onChange={(value) => setResourceDraft({ ...resourceDraft, unit: value })} required />
          <Input label="Available quantity" type="number" value={resourceDraft.available_quantity} onChange={(value) => setResourceDraft({ ...resourceDraft, available_quantity: value })} required />
          <Input label="Storage location" value={resourceDraft.storage_location} onChange={(value) => setResourceDraft({ ...resourceDraft, storage_location: value })} required />
          <button className="primary-action" type="submit"><Package size={17} /> Add resource</button>
        </form>
      </section>

      <section className="panel">
        <PanelTitle eyebrow="Dispatch baseline" title="Register a responder unit" />
        <p className="muted-copy">Available units participate in proximity-based automatic rescue allocation.</p>
        <form className="access-form" onSubmit={onResponderSubmit}>
          <Input label="Unit name" value={responderDraft.name} onChange={(value) => setResponderDraft({ ...responderDraft, name: value })} required />
          <Input label="Unit type" value={responderDraft.unit_type} onChange={(value) => setResponderDraft({ ...responderDraft, unit_type: value })} required />
          <Textarea label="Skills and capabilities" value={responderDraft.skills} onChange={(value) => setResponderDraft({ ...responderDraft, skills: value })} required />
          <Input label="Contact phone" value={responderDraft.contact_phone} onChange={(value) => setResponderDraft({ ...responderDraft, contact_phone: value })} required />
          <Input label="Latitude" type="number" step="any" value={responderDraft.latitude} onChange={(value) => setResponderDraft({ ...responderDraft, latitude: value })} required />
          <Input label="Longitude" type="number" step="any" value={responderDraft.longitude} onChange={(value) => setResponderDraft({ ...responderDraft, longitude: value })} required />
          <button className="primary-action" type="submit"><Siren size={17} /> Register responder</button>
        </form>
      </section>

      <section className="panel">
        <PanelTitle eyebrow="Verified relief" title="Open a donation campaign" />
        <p className="muted-copy">Campaigns accept auditable pledges. Configure an approved payment URL separately before collecting money online.</p>
        <form className="access-form" onSubmit={onCampaignSubmit}>
          <Select label="Related incident" value={campaignDraft.disaster_id} options={disasterOptions} onChange={(value) => setCampaignDraft({ ...campaignDraft, disaster_id: value })} />
          <Input label="Campaign title" value={campaignDraft.title} onChange={(value) => setCampaignDraft({ ...campaignDraft, title: value })} required />
          <Textarea label="Purpose and eligible uses" value={campaignDraft.description} onChange={(value) => setCampaignDraft({ ...campaignDraft, description: value })} required />
          <Input label="Goal amount" type="number" value={campaignDraft.goal_amount} onChange={(value) => setCampaignDraft({ ...campaignDraft, goal_amount: value })} required />
          <Input label="Currency" value={campaignDraft.currency} onChange={(value) => setCampaignDraft({ ...campaignDraft, currency: value })} required />
          <Input label="Verified organizer" value={campaignDraft.organizer} onChange={(value) => setCampaignDraft({ ...campaignDraft, organizer: value })} required />
          <button className="primary-action" type="submit"><HeartPulse size={17} /> Open campaign</button>
        </form>
      </section>
    </div>
  );
}

function MotionPage({ children }) {
  return <div className="motion-page">{children}</div>;
}

function filterAndSortDisasters(disasters, { searchQuery, filters, sortMode }) {
  return sortOperationalItems(
    disasters.filter((item) => {
      const matchesType = filters.type === 'all' || item.disaster_type === filters.type;
      const matchesSeverity = filters.severity === 'all' || normalizeValue(item.label) === filters.severity;
      const matchesStatus = filters.status === 'all' || normalizeValue(item.status) === filters.status;
      const matchesSearch = matchesQuery(searchQuery, [item.title, item.address, item.description, item.disaster_type, item.label, item.status]);
      return matchesType && matchesSeverity && matchesStatus && matchesSearch;
    }),
    sortMode,
    'disaster',
  );
}

function filterAndSortRescues(rescues, disasterLookup, { searchQuery, filters, sortMode }) {
  return sortOperationalItems(
    rescues.filter((item) => {
      const disaster = disasterLookup.get(Number(item.disaster_id));
      const matchesType = filters.type === 'all' || disaster?.disaster_type === filters.type;
      const matchesSeverity = filters.severity === 'all' || normalizeValue(item.priority_label) === filters.severity;
      const matchesStatus = filters.status === 'all' || normalizeValue(item.status) === filters.status;
      const matchesSearch = matchesQuery(searchQuery, [
        item.victim_name,
        item.condition,
        item.status,
        item.priority_label,
        item.assigned_unit,
        item.notes,
        disaster?.title,
        disaster?.address,
      ]);
      return matchesType && matchesSeverity && matchesStatus && matchesSearch;
    }),
    sortMode,
    'rescue',
  );
}

function sortOperationalItems(items, sortMode, kind) {
  return [...items].sort((a, b) => {
    if (sortMode === 'newest') return Number(b.id) - Number(a.id);
    if (sortMode === 'people') {
      const left = kind === 'disaster' ? Number(a.people_affected || 0) : Number(a.people_count || 0);
      const right = kind === 'disaster' ? Number(b.people_affected || 0) : Number(b.people_count || 0);
      return right - left;
    }
    const left = kind === 'disaster' ? Number(a.score || 0) : Number(a.priority_score || 0);
    const right = kind === 'disaster' ? Number(b.score || 0) : Number(b.priority_score || 0);
    return right - left;
  });
}

function matchesQuery(searchQuery, fields) {
  const query = normalizeValue(searchQuery);
  if (!query) return true;
  return fields.some((field) => normalizeValue(field).includes(query));
}

function normalizeValue(value) {
  return String(value || '').trim().toLowerCase();
}

function sortBoardItems(items, direction) {
  const sign = direction === 'asc' ? 1 : -1;
  return [...items].sort((a, b) => (boardScoreValue(a.score) - boardScoreValue(b.score)) * sign);
}

function boardScoreValue(value) {
  const parsed = Number.parseInt(String(value).replace(/\D/g, ''), 10);
  if (Number.isFinite(parsed)) return parsed;
  const normalized = normalizeValue(value);
  if (normalized.includes('critical')) return 100;
  if (normalized.includes('high')) return 80;
  if (normalized.includes('medium')) return 60;
  if (normalized.includes('low')) return 40;
  if (normalized.includes('verified')) return 30;
  return 0;
}

function nextRescueStatus(status) {
  const normalized = normalizeValue(status);
  if (normalized === 'pending') return 'assigned';
  if (normalized === 'assigned' || normalized === 'triage') return 'en route';
  if (normalized === 'en route') return 'rescued';
  return null;
}

function recommendedUnitForRescue(rescue, disaster, role, responderUnits, ambulances) {
  const availableAmbulance = ambulances.find((item) => item.status === 'available');
  const needsAmbulance = role === 'Ambulance' || rescue.condition === 'critical' || rescue.priority_label === 'Critical';
  if (needsAmbulance && availableAmbulance) return availableAmbulance.vehicle_number;

  const availableUnits = responderUnits.filter((item) => item.availability_status === 'available');
  const preferredType = disaster?.disaster_type === 'fire'
    ? 'fire'
    : ['flood', 'cyclone'].includes(disaster?.disaster_type)
      ? 'rescue'
      : role === 'NGO'
        ? 'relief'
        : '';
  const preferred = availableUnits.find((item) => normalizeValue(`${item.unit_type} ${item.skills}`).includes(preferredType));
  return preferred?.name || availableUnits[0]?.name || availableAmbulance?.vehicle_number || null;
}

function nextAmbulanceStatus(status) {
  const order = ['available', 'dispatched', 'maintenance'];
  const currentIndex = order.indexOf(normalizeValue(status));
  return order[(currentIndex + 1) % order.length];
}

function rescueActionLabel(role, rescue, canAssign) {
  if (rescue.status === 'rescued') return 'Done';
  if (canAssign) {
    if (rescue.status === 'pending') return 'Assign';
    if (rescue.status === 'assigned' || rescue.status === 'triage') return 'Send en route';
    if (rescue.status === 'en route') return 'Mark rescued';
  }
  if (role === 'Hospital') return rescue.status === 'triage' ? 'Triaged' : 'Triage';
  if (role === 'Volunteer') return rescue.status === 'en route' ? 'Checked in' : 'Check in';
  if (role === 'Ambulance') return rescue.status === 'rescued' ? 'Completed' : 'Advance status';
  if (role === 'Citizen') return 'Track';
  return 'View';
}

function clampNumber(value, min, max) {
  return Math.max(min, Math.min(max, Number(value)));
}

function readOfflineQueue() {
  try {
    const parsed = JSON.parse(localStorage.getItem(OFFLINE_QUEUE_KEY) || '[]');
    if (!Array.isArray(parsed)) return [];
    const cutoff = Date.now() - OFFLINE_QUEUE_TTL_MS;
    const current = parsed
      .filter((item) => Number(item.queued_at || item.id || 0) >= cutoff)
      .slice(-OFFLINE_QUEUE_LIMIT);
    if (current.length !== parsed.length) localStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(current));
    return current;
  } catch {
    localStorage.removeItem(OFFLINE_QUEUE_KEY);
    return [];
  }
}

function normalizeAlert(alert) {
  return {
    ...alert,
    channel: alert.channel || alert.channels || 'Operations dashboard',
    time: alert.time || (alert.created_at ? new Date(alert.created_at).toLocaleString() : 'Just now'),
  };
}

function normalizeDisaster(disaster) {
  const severity = normalizeValue(disaster.severity_hint || 'medium');
  const fallbackScores = { low: 28, medium: 52, high: 78, critical: 94 };
  const score = Number.isFinite(Number(disaster.score)) ? Number(disaster.score) : fallbackScores[severity] || 52;
  return {
    ...disaster,
    score,
    label: disaster.label || `${severity.charAt(0).toUpperCase()}${severity.slice(1)}`,
  };
}

function buildHourlyResponseTrend(disasters, rescues) {
  const currentHour = new Date();
  currentHour.setMinutes(0, 0, 0);
  const buckets = Array.from({ length: 6 }, (_, index) => {
    const start = new Date(currentHour.getTime() - (5 - index) * 60 * 60 * 1000);
    return {
      start,
      end: new Date(start.getTime() + 60 * 60 * 1000),
      time: start.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      reports: 0,
      rescued: 0,
    };
  });
  const addToBucket = (timestamp, field) => {
    const time = new Date(timestamp);
    if (Number.isNaN(time.getTime())) return;
    const bucket = buckets.find((item) => time >= item.start && time < item.end);
    if (bucket) bucket[field] += 1;
  };
  disasters.forEach((item) => addToBucket(item.created_at, 'reports'));
  rescues.filter((item) => item.status === 'rescued').forEach((item) => addToBucket(item.updated_at || item.created_at, 'rescued'));
  return buckets.map(({ time, reports, rescued }) => ({ time, reports, rescued }));
}

function EmptyState({ title, detail }) {
  return (
    <div className="empty-state">
      <strong>{title}</strong>
      <span>{detail}</span>
    </div>
  );
}

function RoleDashboard({ role, metrics, disasters, rescues, facilities, alerts, resources, responseHub, coordination, setActiveView, onAcknowledge }) {
  const workspace = getRoleWorkspace(role, { metrics, disasters, rescues, facilities, alerts, resources, responseHub, coordination });
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
      {role === 'Citizen' && alerts[0] && (
        <section className="panel citizen-alert-card">
          <div>
            <p className="eyebrow">Authoritative warning · {alerts[0].channel}</p>
            <h2>{alerts[0].audience}</h2>
            <p>{alerts[0].message}</p>
            {alerts[0].instruction && <strong>{alerts[0].instruction}</strong>}
          </div>
          <button className="primary-action" type="button" disabled={alerts[0].acknowledged} onClick={() => onAcknowledge(alerts[0])}>
            <CircleCheck size={18} /> {alerts[0].acknowledged ? 'Receipt confirmed' : 'I received this warning'}
          </button>
        </section>
      )}
    </div>
  );
}

function getRoleWorkspace(role, { metrics, disasters, rescues, facilities, alerts, resources, responseHub, coordination }) {
  const topRescue = rescues[0];
  const activeDisaster = disasters[0];
  const firstHospital = facilities.hospitals[0];
  const firstShelter = facilities.shelters[0];
  const firstAmbulance = facilities.ambulances[0];
  const responderUnits = responseHub?.responder_units || [];
  const volunteers = coordination?.volunteers || [];
  const availableResources = resources.reduce((sum, item) => sum + Number(item.available_quantity || 0), 0);
  const foodResources = resources.filter((item) => /food|rice|meal|water/i.test(`${item.category} ${item.name}`));
  const medicineResources = resources.filter((item) => /medic|health|first aid/i.test(`${item.category} ${item.name}`));
  const resourceQuantity = (items) => items.reduce((sum, item) => sum + Number(item.available_quantity || 0), 0);
  const base = {
    Citizen: {
      icon: Home,
      eyebrow: 'Citizen safety workspace',
      title: 'Get help, follow warnings and reach safe shelter',
      summary: 'Focused on emergency reporting, rescue tracking, official alerts and nearby capacity.',
      metrics: [
        { label: 'Nearest shelter slots', value: metrics.shelterCapacity, detail: firstShelter?.name || 'No shelter registered' },
        { label: 'Hospital beds visible', value: metrics.beds, detail: 'For emergency referral and ambulance handoff' },
        { label: 'Active warnings', value: alerts.length, detail: 'Official messages in your area' },
        { label: 'My request status', value: topRescue?.status || 'None', detail: topRescue?.assigned_unit || 'No active dispatch assigned' },
      ],
      focus: { eyebrow: 'Safety plan', title: 'Immediate citizen actions' },
      second: { eyebrow: 'Nearby support', title: 'Where to go next' },
      tasks: [
        { title: 'Report urgent help with exact location', detail: 'Use the report form before phone battery or network drops.', status: 'High' },
        { title: 'Move vulnerable people first', detail: 'Children, elderly and injured people should move to a verified open shelter.', status: 'Guidance' },
        { title: 'Follow official alert channel', detail: alerts[0]?.message || 'Await an updated warning from command.', status: alerts.length ? 'Active alert' : 'Waiting' },
      ],
      signals: [
        { label: 'Open shelter', value: firstShelter?.available_capacity || 0, detail: firstShelter?.name || 'Shelter capacity', icon: Home },
        { label: 'Medical support', value: firstShelter ? (firstShelter.medical_support ? 'Yes' : 'No') : 'Not registered', detail: 'Shelter medical assistance status', icon: HeartPulse },
        { label: 'Emergency route', value: activeDisaster ? 'Verify locally' : 'No incident', detail: activeDisaster?.address || 'No route has been recorded', icon: Navigation },
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
        { title: 'Activate triage desk', detail: 'Tag critical, delayed and walking wounded arrivals.', status: 'Checklist' },
        { title: 'Prepare overflow care area', detail: 'Use the approved overflow plan if emergency demand rises.', status: 'Review' },
        { title: 'Coordinate patient transfer', detail: 'Share capacity with ambulance and command users.', status: firstHospital ? 'Configured' : 'Missing' },
      ],
      signals: [
        { label: firstHospital?.name || 'Hospital', value: firstHospital?.available_beds || 0, detail: 'Available beds', icon: Building2 },
        { label: 'Emergency capacity', value: firstHospital?.emergency_capacity || 0, detail: 'Immediate intake capacity', icon: Siren },
        { label: 'Referral route', value: 'Not recorded', detail: 'Confirm the interfacility transfer plan offline', icon: Navigation },
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
        { label: 'Food support', value: firstShelter ? (firstShelter.food_available ? 'Available' : 'Unavailable') : 'Not registered', detail: 'Camp meal distribution status' },
        { label: 'Medical support', value: firstShelter ? (firstShelter.medical_support ? 'On site' : 'Referral') : 'Not registered', detail: 'Basic triage capability' },
        { label: 'Expected arrivals', value: metrics.pending + metrics.assigned, detail: 'From active rescue queue' },
      ],
      focus: { eyebrow: 'Relief camp intake', title: 'Shelter action board' },
      second: { eyebrow: 'Camp signals', title: 'Capacity and supplies' },
      tasks: [
        { title: 'Update available capacity', detail: 'Keep command and citizens aware of free slots.', status: firstShelter ? 'Configured' : 'Missing' },
        { title: 'Prepare family intake desk', detail: 'Record vulnerable people and medical needs.', status: 'Checklist' },
        { title: 'Flag supply shortage early', detail: 'Request food, water, blankets or medicines before stockout.', status: 'Medium' },
      ],
      signals: [
        { label: firstShelter?.name || 'Relief shelter', value: firstShelter?.available_capacity || 0, detail: 'Slots available', icon: Home },
        { label: 'Food', value: firstShelter ? (firstShelter.food_available ? 'Available' : 'Unavailable') : 'Not registered', detail: 'Meal support status', icon: Package },
        { label: 'Medical', value: firstShelter ? (firstShelter.medical_support ? 'Available' : 'Referral') : 'Not registered', detail: 'Health desk availability', icon: HeartPulse },
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
        { label: 'Unit status', value: firstAmbulance?.status || 'Not registered', detail: firstAmbulance?.vehicle_number || 'No vehicle linked' },
      ],
      focus: { eyebrow: 'Dispatch queue', title: 'Ambulance action board' },
      second: { eyebrow: 'Handoff signals', title: 'Route and hospital context' },
      tasks: [
        { title: 'Accept highest-priority dispatch', detail: topRescue?.notes || 'No high-priority dispatch waiting.', status: topRescue?.priority_label || 'Waiting' },
        { title: 'Confirm receiving hospital', detail: firstHospital ? `${firstHospital.name} has ${firstHospital.available_beds} beds visible.` : 'No receiving hospital is registered.', status: firstHospital ? 'Review' : 'Missing' },
        { title: 'Update vehicle status', detail: 'Keep availability accurate for command allocation.', status: firstAmbulance?.status || 'Missing' },
      ],
      signals: [
        { label: 'ETA target', value: 'Not recorded', detail: topRescue?.victim_name || 'No assigned call', icon: Navigation },
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
        { label: 'Food and water stock', value: resourceQuantity(foodResources), detail: `${foodResources.length} verified inventory records` },
        { label: 'Medical stock', value: resourceQuantity(medicineResources), detail: `${medicineResources.length} verified inventory records` },
        { label: 'Open shelters', value: facilities.shelters.length, detail: `${metrics.shelterCapacity} free slots` },
        { label: 'Unmet needs', value: metrics.pending, detail: 'Pending high-priority requests' },
      ],
      focus: { eyebrow: 'Relief distribution', title: 'NGO action board' },
      second: { eyebrow: 'Coordination signals', title: 'Where support is needed' },
      tasks: [
        { title: 'Dispatch food and water to open shelters', detail: 'Prioritize high-occupancy camps and flood zones.', status: 'High' },
        { title: 'Assign volunteers to intake and logistics', detail: 'Match skills to shelter, WASH and relief tasks.', status: volunteers.length ? 'Available' : 'Waiting' },
        { title: 'Submit field assessment', detail: 'Report unmet household needs from the affected ward.', status: 'Guidance' },
      ],
      signals: [
        { label: 'Relief stock', value: availableResources, detail: `${resources.length} inventory records`, icon: Package },
        { label: 'Volunteer teams', value: volunteers.length, detail: 'Verified volunteer profiles visible', icon: Users },
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
        { label: 'Assigned tasks', value: rescues.length, detail: topRescue?.notes || 'No active assignment' },
        { label: 'Safety briefing', value: 'Not recorded', detail: 'Confirm briefing with the incident supervisor' },
        { label: 'Nearest shelter', value: firstShelter?.available_capacity || 0, detail: firstShelter?.name || 'Open shelter' },
        { label: 'Check-in', value: topRescue?.status || 'No assignment', detail: topRescue?.assigned_unit || 'No response unit assigned' },
      ],
      focus: { eyebrow: 'Assignment board', title: 'Volunteer action board' },
      second: { eyebrow: 'Safety signals', title: 'Before deployment' },
      tasks: [
        { title: 'Confirm availability', detail: 'Check in before moving to the assigned area.', status: topRescue ? 'Assigned' : 'Waiting' },
        { title: 'Support shelter intake', detail: 'Help families register and identify vulnerable people when assigned.', status: 'Guidance' },
        { title: 'Report unsafe conditions', detail: 'Escalate blocked roads, live wires or contaminated water.', status: 'Guidance' },
      ],
      signals: [
        { label: 'PPE status', value: 'Not recorded', detail: 'Confirm PPE with the incident supervisor', icon: ClipboardList },
        { label: 'Task area', value: activeDisaster ? 'Assigned area' : 'None', detail: activeDisaster?.address || 'No task location recorded', icon: Navigation },
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
        { label: 'Road corridors', value: 'Not recorded', detail: 'Validate closures through the authorized traffic system' },
        { label: 'Alerts sent', value: alerts.length, detail: 'Public warnings visible' },
      ],
      focus: { eyebrow: 'Public-safety board', title: 'Police action board' },
      second: { eyebrow: 'Access signals', title: 'Perimeters and movement' },
      tasks: [
        { title: 'Secure rescue corridor', detail: 'Keep route open for ambulance and fire rescue access.', status: 'High' },
        { title: 'Manage evacuation perimeter', detail: 'Guide citizens away from unstable or flooded areas.', status: activeDisaster ? 'Review' : 'Waiting' },
        { title: 'Verify public warning reach', detail: 'Confirm ward-level warnings are understood and actionable.', status: alerts.length ? 'Review' : 'Waiting' },
      ],
      signals: [
        { label: 'Primary corridor', value: activeDisaster ? 'Unverified' : 'None', detail: activeDisaster?.address || 'No incident access route', icon: Navigation },
        { label: 'Crowd control', value: 'Not recorded', detail: 'No perimeter status has been entered', icon: Users },
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
        { label: 'Rescue teams', value: responderUnits.length, detail: 'Registered professional responder units' },
        { label: 'Equipment ready', value: 'Not recorded', detail: 'Equipment inspection is not yet recorded' },
      ],
      focus: { eyebrow: 'Fire rescue board', title: 'Rescue action board' },
      second: { eyebrow: 'Hazard signals', title: 'Scene safety and equipment' },
      tasks: [
        { title: 'Prioritize trapped victims', detail: topRescue?.notes || 'No trapped victim in queue.', status: topRescue?.priority_label || 'Waiting' },
        { title: 'Stage rescue equipment', detail: 'Check PPE, boat, rope and extrication gear readiness.', status: 'Checklist' },
        { title: 'Update scene status', detail: 'Share hazard, smoke, floodwater and structural risk changes.', status: activeDisaster ? 'Review' : 'Waiting' },
      ],
      signals: [
        { label: 'Scene hazard', value: topRescue?.priority_label || 'Medium', detail: activeDisaster?.title || 'Active incident', icon: AlertTriangle },
        { label: 'Team ETA', value: 'Not recorded', detail: topRescue?.assigned_unit || 'No response team assigned', icon: Navigation },
        { label: 'Equipment', value: 'Not recorded', detail: 'Record readiness through the incident supervisor', icon: Package },
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
  if (['Citizen', 'Hospital', 'Volunteer', 'Ambulance'].includes(role)) return rescues;
  if (role === 'Shelter') return rescues.filter((item) => item.condition === 'stable' || item.status === 'en route');
  return rescues;
}

function CommandView({
  metrics,
  disasters,
  rescues,
  facilities,
  resources,
  readinessPillars,
  fieldTeams,
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
  filterSummary,
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
          <h2>India-wide live risk and relief readiness</h2>
          <span>GIS map, resources, alerts, health capacity, and field teams across affected districts in India.</span>
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

      <section className="metrics-grid metrics-grid-5">
        <MetricTile icon={Activity} label="Active disasters" value={disasters.length} detail={filterSummary} />
        <MetricTile icon={HeartPulse} label="Critical rescues" value={metrics.critical} detail={`${metrics.pending} pending requests`} />
        <MetricTile icon={Ambulance} label="Ambulances ready" value={metrics.availableAmbulances} detail={`${metrics.assigned} units assigned/en route`} />
        <MetricTile icon={Home} label="Shelter capacity" value={metrics.shelterCapacity} detail={`${metrics.totalShelterCapacity} total relief slots`} />
        <MetricTile icon={Building2} label="Hospital beds" value={metrics.beds} detail={`${metrics.totalBeds} total beds tracked`} />
      </section>

      {dashboardMode === 'overview' && (
        <>
          <ResponseBoard disasters={disasters} rescues={rescues} reduceMotion={reduceMotion} />
          <MapDecisionSection disasters={disasters} rescues={rescues} allocation={allocation} reduceMotion={reduceMotion} />
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
            <EarlyWarningPanel pillars={readinessPillars} />
          </section>
        </>
      )}

      {dashboardMode === 'response' && (
        <>
          <ResponseBoard disasters={disasters} rescues={rescues} reduceMotion={reduceMotion} />
          <MapDecisionSection disasters={disasters} rescues={rescues} allocation={allocation} reduceMotion={reduceMotion} />
          <section className="split-grid split-grid-3">
            <FieldTeamsPanel teams={fieldTeams} />
            <StandardsPanel />
            <AlertComposer alerts={alerts} draft={alertDraft} setDraft={setAlertDraft} onSubmit={sendAlert} />
          </section>
        </>
      )}

      {dashboardMode === 'health' && (
        <>
          <section className="split-grid split-grid-3">
            <FacilityCapacityPanel facilities={facilities} />
            <TriagePanel rescues={rescues} disasters={disasters} />
            <EarlyWarningPanel pillars={readinessPillars} />
          </section>
          <section className="analytics-wall">
            <PanelTitle eyebrow="Health trend" title="Emergency response trend" />
            <div className="chart-box chart-box-wide">
              <Line data={trendChart} options={chartOptions} />
            </div>
          </section>
        </>
      )}

      {dashboardMode === 'logistics' && (
        <>
          <section className="operations-grid">
            <ResourceReadinessPanel resources={resources} />
            <FieldTeamsPanel teams={fieldTeams} />
            <StandardsPanel />
            <AlertComposer alerts={alerts} draft={alertDraft} setDraft={setAlertDraft} onSubmit={sendAlert} />
          </section>
          <MapDecisionSection disasters={disasters} rescues={rescues} allocation={allocation} reduceMotion={reduceMotion} />
        </>
      )}
    </div>
  );
}

function MapDecisionSection({ disasters, rescues, allocation, reduceMotion }) {
  return (
    <section className="main-grid command-grid">
      <motion.div className="panel map-panel" layout transition={reduceMotion ? quickFade : softSpring}>
        <div className="panel-header">
          <div>
            <p>Live India incident map</p>
            <h2>Reports, rescues and impact locations</h2>
          </div>
          <StatusPill value="Live GIS" />
        </div>
        <MapContainer center={[22.9734, 78.6569]} zoom={5} scrollWheelZoom={false} className="incident-map">
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
        {!disasters.length && !rescues.length && <EmptyState title="No map results" detail="No live incident or rescue location matches the current view." />}
      </motion.div>

      <DecisionStack allocation={allocation} rescues={rescues} disasters={disasters} />
    </section>
  );
}

function FacilityCapacityPanel({ facilities }) {
  return (
    <section className="panel">
      <PanelTitle eyebrow="Health capacity" title="Hospitals and relief camps" />
      <div className="facility-snapshot-list">
        {facilities.hospitals.map((item) => {
          const percent = Math.round((item.available_beds / item.total_beds) * 100);
          return (
            <div className="facility-snapshot" key={item.id}>
              <Building2 size={17} />
              <div>
                <strong>{item.name}</strong>
                <span>{item.available_beds}/{item.total_beds} beds, ICU {item.icu_beds}</span>
                <ProgressBar value={percent} />
              </div>
            </div>
          );
        })}
        {facilities.shelters.map((item) => {
          const percent = Math.round((item.available_capacity / item.total_capacity) * 100);
          return (
            <div className="facility-snapshot" key={`s-${item.id}`}>
              <Home size={17} />
              <div>
                <strong>{item.name}</strong>
                <span>{item.available_capacity}/{item.total_capacity} relief slots</span>
                <ProgressBar value={percent} />
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function TriagePanel({ rescues, disasters }) {
  const triageItems = rescues.filter((item) => ['Critical', 'High'].includes(item.priority_label)).slice(0, 5);
  return (
    <section className="panel">
      <PanelTitle eyebrow="Clinical triage" title="Incoming high-risk rescues" />
      <div className="role-task-list">
        {triageItems.map((item) => (
          <div className="role-task" key={item.id}>
            <StatusPill value={item.priority_label} />
            <div>
              <strong>{item.victim_name}</strong>
              <span>{disasters.find((disaster) => disaster.id === Number(item.disaster_id))?.title || 'Linked incident'} - {item.notes}</span>
            </div>
          </div>
        ))}
        {!triageItems.length && <EmptyState title="No high-risk rescues" detail="Current filters do not include Critical or High rescue requests." />}
      </div>
    </section>
  );
}

function ResponseBoard({ disasters, rescues, reduceMotion }) {
  const columns = getResponseBoardColumns(disasters, rescues);
  const [sortConfig, setSortConfig] = useState({ columnId: 'reported', direction: 'desc' });
  const [inspectedItem, setInspectedItem] = useState(null);

  function toggleColumnSort(columnId) {
    setSortConfig((current) => ({
      columnId,
      direction: current.columnId === columnId && current.direction === 'desc' ? 'asc' : 'desc',
    }));
  }

  return (
    <>
      <section className="response-board" aria-label="Emergency response stages">
        {columns.map((column) => {
          const items = sortConfig.columnId === column.id ? sortBoardItems(column.items, sortConfig.direction) : column.items;
          return (
            <div className="response-column" key={column.id}>
              <div className="response-column-header">
                <div>
                  <h2>{column.title}</h2>
                  <span>{column.subtitle}</span>
                </div>
                <button
                  type="button"
                  className={sortConfig.columnId === column.id ? 'active' : ''}
                  aria-label={`Sort ${column.title}`}
                  onClick={() => toggleColumnSort(column.id)}
                >
                  {column.items.length}
                  <ArrowUpDown size={13} />
                </button>
              </div>
              <div className="response-card-list">
                {items.map((item) => (
                  <ResponseCard key={item.id} item={item} reduceMotion={reduceMotion} onInspect={setInspectedItem} />
                ))}
                {!items.length && <EmptyState title="Nothing here" detail="No records match this stage with the current filters." />}
              </div>
            </div>
          );
        })}
      </section>
      {inspectedItem && (
        <section className="board-inspector" aria-live="polite">
          <div>
            <p className="eyebrow">Focused record</p>
            <h2>{inspectedItem.title}</h2>
            <span>{inspectedItem.description}</span>
          </div>
          <div className="board-inspector-meta">
            <StatusPill value={inspectedItem.status} />
            <strong>{inspectedItem.score}</strong>
            <button type="button" className="compact-button secondary-button" onClick={() => setInspectedItem(null)}>
              Close
            </button>
          </div>
        </section>
      )}
    </>
  );
}

function ResponseCard({ item, reduceMotion, onInspect }) {
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
        <button type="button" aria-label={`More actions for ${item.title}`} onClick={() => onInspect(item)}>
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
    updates: item.sync_status === 'queued' ? 'Queued for reconnection' : `${item.status} status`,
    people: item.people_affected,
    status: item.sync_status === 'queued' ? 'Queued offline' : item.label,
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
      updates: item.trapped ? 'Trapped reported' : 'Not trapped',
      people: item.people_count,
      status: item.sync_status === 'queued' ? 'Queued offline' : item.priority_label,
      score: `${item.priority_score}/100`,
      dark: index === 0,
    }));

  const dispatchedCards = rescues
    .filter((item) => ['assigned', 'en route', 'triage'].includes(item.status))
    .slice(0, 3)
    .map((item) => ({
      id: `dispatch-${item.id}`,
      title: item.assigned_unit || 'Dispatch pending',
      kicker: item.victim_name,
      description: item.notes,
      time: item.created_at,
      updates: item.status,
      people: item.people_count,
      status: item.status,
      score: item.priority_label,
    }));

  const coordinatedCards = rescues
    .filter((item) => item.status === 'rescued')
    .slice(0, 3)
    .map((item) => ({
      id: `coordinated-${item.id}`,
      title: item.victim_name,
      kicker: 'completed rescue',
      description: item.notes || 'Rescue completed and recorded by the response team.',
      time: item.updated_at || item.created_at,
      updates: item.assigned_unit || 'Response team',
      people: item.people_count,
      status: 'Rescued',
      score: item.priority_label,
    }));

  return [
    { id: 'reported', title: 'Reported', subtitle: 'Incoming field reports', items: reportCards },
    { id: 'prioritized', title: 'Prioritized', subtitle: 'AI-ranked rescue needs', items: prioritizedCards },
    { id: 'dispatched', title: 'Dispatched', subtitle: 'Teams and vehicles moving', items: dispatchedCards },
    { id: 'coordinated', title: 'Coordinated', subtitle: 'Completed and verified response', items: coordinatedCards },
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

function EarlyWarningPanel({ pillars }) {
  return (
    <section className="panel">
      <PanelTitle eyebrow="Early warning" title="Readiness pillars" />
      <div className="readiness-list">
        {pillars.map(({ name, score, detail, icon: Icon }) => (
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

function ResourceReadinessPanel({ resources = [] }) {
  const inventory = resources.map((resource) => ({
    name: resource.name,
    available: Number(resource.available_quantity || 0),
    unit: resource.unit,
    location: resource.storage_location,
  }));
  return (
    <section className="panel">
      <PanelTitle eyebrow="Logistics" title="Resource inventory health" />
      <div className="inventory-list">
        {inventory.map((item) => (
            <div className="inventory-row" key={item.name}>
              <div>
                <strong>{item.name}</strong>
                <span>{item.available.toLocaleString()} {item.unit} available{item.location ? ` at ${item.location}` : ''}</span>
              </div>
            </div>
        ))}
        {!inventory.length && <EmptyState title="No resource inventory" detail="Add verified stock in Operational Setup before planning distributions." />}
      </div>
    </section>
  );
}

function FieldTeamsPanel({ teams = [] }) {
  return (
    <section className="panel">
      <PanelTitle eyebrow="Field operations" title="Registered responder readiness" />
      <div className="team-list">
        {teams.map((team) => (
          <div className="team-row" key={team.name}>
            <div className="team-status-dot" />
            <div>
              <strong>{team.name}</strong>
              <span>{team.unit_type || 'Responder unit'} · {team.latitude != null && team.longitude != null ? 'Location registered' : 'Location not registered'}</span>
            </div>
            <StatusPill value={team.availability_status || 'unknown'} />
          </div>
        ))}
        {!teams.length && <EmptyState title="No responder units" detail="Register verified field units in Operational Setup to enable proximity dispatch." />}
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
        <Textarea label="Action instruction" value={draft.instruction} onChange={(value) => setDraft({ ...draft, instruction: value })} required />
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
              <span>{alert.channel} - {alert.time}{alert.acknowledgement_count != null ? ` · ${alert.acknowledgement_count} confirmed` : ''}</span>
              <p>{alert.message}</p>
              {alert.instruction && <p><strong>Action:</strong> {alert.instruction}</p>}
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

function ReportView({ draft, setDraft, onSubmit, rescueDraft, setRescueDraft, disasters, onRescueSubmit, routeResult, onFindSafeRoute, onUseDeviceLocation }) {
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
          <Input label="Latitude" type="number" step="any" value={draft.latitude} onChange={(value) => setDraft({ ...draft, latitude: value })} />
          <Input label="Longitude" type="number" step="any" value={draft.longitude} onChange={(value) => setDraft({ ...draft, longitude: value })} />
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
        <button className="location-consent-button" type="button" onClick={onUseDeviceLocation}>
          <Crosshair size={18} /> {rescueDraft.location_consent ? `Device location captured · ±${rescueDraft.location_accuracy || '?'} m` : 'Share my device location with responders'}
        </button>
        <p className="consent-copy">Location is shared only after browser permission and is attached to this emergency request.</p>
        <div className="form-row">
          <Input label="Vulnerable people" type="number" value={rescueDraft.vulnerable_people} onChange={(value) => setRescueDraft({ ...rescueDraft, vulnerable_people: value })} />
          <Input label="Latitude" type="number" step="any" value={rescueDraft.latitude} onChange={(value) => setRescueDraft({ ...rescueDraft, latitude: value })} />
          <Input label="Longitude" type="number" step="any" value={rescueDraft.longitude} onChange={(value) => setRescueDraft({ ...rescueDraft, longitude: value })} />
        </div>
        <Textarea label="Notes" value={rescueDraft.notes} onChange={(value) => setRescueDraft({ ...rescueDraft, notes: value })} />
        <button className="primary-action" type="submit">
          <HeartPulse size={18} /> Submit rescue request
        </button>
      </form>

      <section className="panel form-panel safe-route-panel">
        <div className="panel-header">
          <div>
            <p>Last-mile safety</p>
            <h2>Find an available safe destination</h2>
          </div>
        </div>
        <p className="route-guidance">Uses the request coordinates and live capacity to locate the nearest available facility. Always follow official closures and responder instructions.</p>
        <div className="route-actions">
          <button className="primary-action" type="button" onClick={() => onFindSafeRoute('shelter')}>
            <Route size={18} /> Find shelter
          </button>
          <button className="secondary-button compact-button" type="button" onClick={() => onFindSafeRoute('hospital')}>
            <HeartPulse size={18} /> Find hospital
          </button>
        </div>
        {routeResult && (
          <div className="route-result">
            <CircleCheck size={20} />
            <div>
              <strong>{routeResult.destination.name}</strong>
              <span>{routeResult.distance_km} km away · {routeResult.nearby_hazards.length} nearby active hazard{routeResult.nearby_hazards.length === 1 ? '' : 's'}</span>
              <p>{routeResult.guidance}</p>
              <a href={routeResult.navigation_url} target="_blank" rel="noreferrer">Open turn-by-turn directions</a>
            </div>
          </div>
        )}
      </section>
    </section>
  );
}

function RescueView({ role, rescues, disasters, selectedRescueId, onAction, onSelect }) {
  const canAssign = assignCapableRoles.has(role);
  const title = role === 'Citizen' ? 'My rescue tracking' : role === 'Hospital' ? 'Incoming triage requests' : role === 'Volunteer' ? 'Volunteer tasks' : 'Rescue requests';
  const eyebrow = role === 'Citizen' ? 'Live status' : role === 'Hospital' ? 'Hospital triage' : role === 'Volunteer' ? 'Assignment queue' : 'AI ranked queue';
  const selectedRescue = rescues.find((item) => item.id === selectedRescueId) || rescues[0];

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
              <tr key={item.id} className={selectedRescue?.id === item.id ? 'selected-row' : ''} onClick={() => onSelect(item.id)}>
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
                  <StatusPill value={item.sync_status === 'queued' ? 'Queued offline' : item.status} />
                </td>
                <td>{item.assigned_unit || 'Unassigned'}</td>
                <td>
                  <button
                    type="button"
                    className="compact-button"
                    disabled={item.status === 'rescued' || item.sync_status === 'queued'}
                    onClick={(event) => {
                      event.stopPropagation();
                      onAction(item.id, role);
                    }}
                  >
                    {item.sync_status === 'queued' ? 'Waiting for connection' : rescueActionLabel(role, item, canAssign)}
                  </button>
                </td>
              </tr>
            ))}
            {!rescues.length && (
              <tr>
                <td colSpan="6">
                  <EmptyState title="No rescue requests" detail="Clear search or filters, or submit a rescue request from the report screen." />
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {selectedRescue && (
        <section className="rescue-detail-strip" aria-live="polite">
          <div>
            <p className="eyebrow">Selected request</p>
            <h3>{selectedRescue.victim_name}</h3>
            <span>{selectedRescue.notes || 'No notes provided.'}</span>
          </div>
          <div className="rescue-detail-meta">
            <StatusPill value={selectedRescue.priority_label} />
            <StatusPill value={selectedRescue.sync_status === 'queued' ? 'Queued offline' : selectedRescue.status} />
            <strong>{selectedRescue.assigned_unit || 'Awaiting unit'}</strong>
          </div>
        </section>
      )}
    </section>
  );
}

function CoordinationView({
  disasters,
  resources,
  coordination,
  distributionDraft,
  setDistributionDraft,
  volunteerDraft,
  setVolunteerDraft,
  onDistributionSubmit,
  onVolunteerSubmit,
}) {
  const availableVolunteers = coordination.volunteers.filter((item) => item.availability_status === 'available');
  return (
    <section className="view-stack">
      <section className="command-hero">
        <div>
          <p className="eyebrow">Shared logistics workspace</p>
          <h2>Move supplies and people to verified needs</h2>
          <span>Inventory is decremented when dispatched and volunteer availability changes when an assignment is accepted.</span>
        </div>
        <div className="hero-score-grid">
          <HeroScore label="Resource types" value={resources.length} icon={Package} />
          <HeroScore label="Volunteers ready" value={availableVolunteers.length} icon={Users} />
          <HeroScore label="Active dispatches" value={coordination.distributions.filter((item) => item.status !== 'delivered').length} icon={Navigation} />
        </div>
      </section>

      <section className="form-grid coordination-forms">
        <form className="panel form-panel" onSubmit={onDistributionSubmit}>
          <PanelTitle eyebrow="Resource dispatch" title="Plan relief distribution" />
          <Select
            label="Resource"
            value={distributionDraft.resource_id}
            options={resources.map((item) => ({ label: `${item.name} · ${item.available_quantity} ${item.unit} available`, value: item.id }))}
            onChange={(value) => setDistributionDraft({ ...distributionDraft, resource_id: value })}
          />
          <Select
            label="Incident"
            value={distributionDraft.disaster_id}
            options={disasters.map((item) => ({ label: item.title, value: item.id }))}
            onChange={(value) => setDistributionDraft({ ...distributionDraft, disaster_id: value })}
          />
          <div className="form-row form-row-2">
            <Input label="Quantity" type="number" value={distributionDraft.quantity} onChange={(value) => setDistributionDraft({ ...distributionDraft, quantity: value })} required />
            <Input label="Destination" value={distributionDraft.destination} onChange={(value) => setDistributionDraft({ ...distributionDraft, destination: value })} required />
          </div>
          <button className="primary-action" type="submit" disabled={!resources.length || !disasters.length}>
            <Package size={18} /> Dispatch inventory
          </button>
        </form>

        <form className="panel form-panel" onSubmit={onVolunteerSubmit}>
          <PanelTitle eyebrow="Field assignment" title="Assign an available volunteer" />
          <Select
            label="Volunteer"
            value={volunteerDraft.volunteer_id}
            options={availableVolunteers.map((item) => ({ label: `${item.name} · ${item.skills}`, value: item.id }))}
            onChange={(value) => setVolunteerDraft({ ...volunteerDraft, volunteer_id: value })}
          />
          <Select
            label="Incident"
            value={volunteerDraft.disaster_id}
            options={disasters.map((item) => ({ label: item.title, value: item.id }))}
            onChange={(value) => setVolunteerDraft({ ...volunteerDraft, disaster_id: value })}
          />
          <Textarea label="Task" value={volunteerDraft.task} onChange={(value) => setVolunteerDraft({ ...volunteerDraft, task: value })} required />
          <button className="primary-action" type="submit" disabled={!availableVolunteers.length || !disasters.length}>
            <Users size={18} /> Create assignment
          </button>
          {!availableVolunteers.length && <p className="route-guidance">No unassigned volunteers are currently available.</p>}
        </form>
      </section>

      <section className="split-grid">
        <section className="panel">
          <PanelTitle eyebrow="Dispatch ledger" title="Recent distributions" />
          <div className="facility-list">
            {coordination.distributions.slice(0, 8).map((item) => (
              <div className="facility-item" key={item.id}>
                <div>
                  <strong>{item.destination}</strong>
                  <span>{item.quantity} units · incident #{item.disaster_id}</span>
                </div>
                <StatusPill value={item.status} />
              </div>
            ))}
            {!coordination.distributions.length && <EmptyState title="No dispatches yet" detail="Plan a distribution to create the shared logistics record." />}
          </div>
        </section>
        <section className="panel">
          <PanelTitle eyebrow="Volunteer ledger" title="Recent assignments" />
          <div className="facility-list">
            {coordination.assignments.slice(0, 8).map((item) => (
              <div className="facility-item" key={item.id}>
                <div>
                  <strong>{item.task}</strong>
                  <span>Volunteer #{item.volunteer_id} · incident #{item.disaster_id}</span>
                </div>
                <StatusPill value={item.status} />
              </div>
            ))}
            {!coordination.assignments.length && <EmptyState title="No assignments yet" detail="Assign an available volunteer to an active incident." />}
          </div>
        </section>
      </section>
    </section>
  );
}

function ResponseHubView({
  role,
  disasters,
  alerts,
  hub,
  welfareDraft,
  setWelfareDraft,
  supplyDraft,
  setSupplyDraft,
  donationDraft,
  setDonationDraft,
  newsDraft,
  setNewsDraft,
  onWelfareSubmit,
  onWelfareAdvance,
  onSupplySubmit,
  onSupplyAdvance,
  onHospitalAcknowledge,
  onDonationSubmit,
  onNewsSubmit,
  onUseDeviceLocation,
}) {
  const canHandleWelfare = ['Admin', 'Police', 'Fire Service', 'NGO', 'Volunteer'].includes(role);
  const canHandleSupplies = ['Admin', 'NGO', 'Shelter', 'Police', 'Fire Service'].includes(role);
  const canPublishNews = role !== 'Citizen';
  const canSeeHospitalPrep = ['Admin', 'Hospital', 'Ambulance'].includes(role);
  const canAcknowledgeHospitalPrep = ['Admin', 'Hospital'].includes(role);
  const campaign = hub.campaigns?.find((item) => Number(item.id) === Number(donationDraft.campaign_id)) || hub.campaigns?.[0];
  const hotline = hub.emergency_hotline || '112';

  return (
    <section className="view-stack response-hub-view">
      <section className="command-hero response-hub-hero">
        <div>
          <p className="eyebrow">National response network</p>
          <h2>Alerts, live field news, family tracing, rescue aid, and verified relief</h2>
          <span>Country-wide incidents are consolidated here while private welfare and supply cases remain role-restricted.</span>
          <div className="hub-actions">
            <a className="emergency-call" href={`tel:${hotline}`}><PhoneCallIcon /> Call emergency responders · {hotline}</a>
          </div>
        </div>
        <div className="hero-score-grid">
          <HeroScore label="Active alerts" value={alerts.length} icon={Bell} />
          <HeroScore label="Live sources" value={(hub.news_updates || []).filter((item) => item.is_live).length} icon={RadioTower} />
          <HeroScore label="Aid cases" value={(hub.supply_requests || []).filter((item) => item.status !== 'delivered').length} icon={Package} />
        </div>
      </section>

      <section className="hub-grid hub-grid-wide">
        <section className="panel hub-panel">
          <PanelTitle eyebrow="All-India warning feed" title="Disaster alerts across the country" />
          <div className="hub-feed">
            {alerts.slice(0, 8).map((alert) => (
              <article className="hub-feed-item alert-item" key={alert.id}>
                <div className="hub-item-heading">
                  <div><strong>{alert.event || alert.audience}</strong><span>{alert.audience} · {alert.channel || alert.channels}</span></div>
                  <StatusPill value={alert.severity || 'severe'} />
                </div>
                <p>{alert.message}</p>
                {alert.instruction && <small><strong>Action:</strong> {alert.instruction}</small>}
              </article>
            ))}
          </div>
        </section>

        <section className="panel hub-panel">
          <PanelTitle eyebrow="Verified area coverage" title="Live disaster news and field updates" />
          <div className="hub-feed">
            {(hub.news_updates || []).slice(0, 8).map((item) => (
              <article className="hub-feed-item" key={item.id}>
                <div className="hub-item-heading">
                  <div><strong>{item.headline}</strong><span>{item.district}, {item.state} · {item.source_name}</span></div>
                  <StatusPill value={item.is_live ? 'Live' : 'Verified'} />
                </div>
                <p>{item.summary}</p>
                {item.stream_url && <a className="stream-link" href={item.stream_url} target="_blank" rel="noreferrer"><RadioTower size={16} /> Open live stream</a>}
              </article>
            ))}
            {!(hub.news_updates || []).length && <EmptyState title="No verified updates" detail="Authorized field desks can publish a stream or situation update." />}
          </div>
        </section>
      </section>

      {role === 'Citizen' && (
        <section className="hub-grid">
          <form className="panel form-panel" onSubmit={onWelfareSubmit}>
            <PanelTitle eyebrow="Family tracing" title="Ask call responders to check a relative" />
            <Select label="Alerted disaster area" value={welfareDraft.disaster_id} options={disasters.map((item) => ({ label: item.title, value: item.id }))} onChange={(value) => setWelfareDraft({ ...welfareDraft, disaster_id: value })} />
            <div className="form-row form-row-2">
              <Input label="Relative's full name" value={welfareDraft.relative_name} onChange={(value) => setWelfareDraft({ ...welfareDraft, relative_name: value })} required />
              <Input label="Relationship" value={welfareDraft.relationship} onChange={(value) => setWelfareDraft({ ...welfareDraft, relationship: value })} required />
            </div>
            <Input label="Relative's phone (if known)" value={welfareDraft.relative_phone} onChange={(value) => setWelfareDraft({ ...welfareDraft, relative_phone: value })} />
            <Input label="Last known location" value={welfareDraft.last_known_location} onChange={(value) => setWelfareDraft({ ...welfareDraft, last_known_location: value })} required />
            <Input label="Your callback number" value={welfareDraft.requester_phone} onChange={(value) => setWelfareDraft({ ...welfareDraft, requester_phone: value })} required />
            <div className="hub-form-actions">
              <button className="location-consent-button" type="button" onClick={() => onUseDeviceLocation('welfare')}><Crosshair size={17} /> Add last-known coordinates</button>
              <a className="compact-button secondary-button call-link" href={`tel:${hotline}`}>Call {hotline}</a>
            </div>
            <label className="toggle-row"><input type="checkbox" checked={welfareDraft.consent_to_contact} onChange={(event) => setWelfareDraft({ ...welfareDraft, consent_to_contact: event.target.checked })} /> I consent to responders contacting me and searching operational records.</label>
            <button className="primary-action" type="submit"><Users size={18} /> Open welfare-check case</button>
          </form>

          <form className="panel form-panel" onSubmit={onSupplySubmit}>
            <PanelTitle eyebrow="Isolated survivor aid" title="Request food, water, medicine, or supplies" />
            <Select label="Linked disaster" value={supplyDraft.disaster_id} options={disasters.map((item) => ({ label: item.title, value: item.id }))} onChange={(value) => setSupplyDraft({ ...supplyDraft, disaster_id: value })} />
            <div className="form-row form-row-2">
              <Select label="Supply type" value={supplyDraft.category} options={['food and water', 'medicine', 'baby supplies', 'mobility support', 'sanitation', 'other']} onChange={(value) => setSupplyDraft({ ...supplyDraft, category: value })} />
              <Select label="Urgency" value={supplyDraft.urgency} options={['medium', 'high', 'critical']} onChange={(value) => setSupplyDraft({ ...supplyDraft, urgency: value })} />
            </div>
            <Textarea label="What is needed and access constraints" value={supplyDraft.description} onChange={(value) => setSupplyDraft({ ...supplyDraft, description: value })} required />
            <div className="form-row form-row-2">
              <Input label="People waiting" type="number" value={supplyDraft.people_count} onChange={(value) => setSupplyDraft({ ...supplyDraft, people_count: value })} required />
              <Input label="Contact phone" value={supplyDraft.contact_phone} onChange={(value) => setSupplyDraft({ ...supplyDraft, contact_phone: value })} required />
            </div>
            <button className="location-consent-button" type="button" onClick={() => onUseDeviceLocation('supply')}><Crosshair size={18} /> {supplyDraft.location_consent ? `Location captured · ±${supplyDraft.location_accuracy || '?'} m` : 'Share exact device location for delivery'}</button>
            <p className="consent-copy">Your browser asks permission first. Coordinates are visible only to authorized response roles.</p>
            <button className="primary-action" type="submit"><Package size={18} /> Send urgent supply request</button>
          </form>
        </section>
      )}

      <section className="hub-grid">
        <section className="panel donation-card">
          <PanelTitle eyebrow="Transparent relief funding" title="Fund future rescues and victim support" />
          {campaign ? (
            <>
              <h3>{campaign.title}</h3>
              <p>{campaign.description}</p>
              <div className="donation-progress-copy"><strong>{formatCurrency(Number(campaign.confirmed_amount || 0), campaign.currency)}</strong><span>confirmed of {formatCurrency(Number(campaign.goal_amount || 0), campaign.currency)}</span></div>
              <ProgressBar value={(Number(campaign.confirmed_amount || 0) / Math.max(1, Number(campaign.goal_amount || 0))) * 100} />
              <span className="pledge-copy">Plus {formatCurrency(Number(campaign.pledged_amount || 0), campaign.currency)} pledged and awaiting confirmation.</span>
            </>
          ) : <EmptyState title="No active campaign" detail="Verified organizers can activate a relief campaign." />}
        </section>
        <form className="panel form-panel" onSubmit={onDonationSubmit}>
          <PanelTitle eyebrow="Donation pledge" title="Support verified response work" />
          <Select label="Campaign" value={donationDraft.campaign_id} options={(hub.campaigns || []).map((item) => ({ label: item.title, value: item.id }))} onChange={(value) => setDonationDraft({ ...donationDraft, campaign_id: value })} />
          <div className="form-row form-row-2"><Input label="Name" value={donationDraft.donor_name} onChange={(value) => setDonationDraft({ ...donationDraft, donor_name: value })} required /><Input label="Email receipt" type="email" value={donationDraft.donor_email} onChange={(value) => setDonationDraft({ ...donationDraft, donor_email: value })} required /></div>
          <Input label="Amount (INR)" type="number" value={donationDraft.amount} onChange={(value) => setDonationDraft({ ...donationDraft, amount: value })} required />
          <Textarea label="Message (optional)" value={donationDraft.message} onChange={(value) => setDonationDraft({ ...donationDraft, message: value })} />
          <label className="toggle-row"><input type="checkbox" checked={donationDraft.anonymous} onChange={(event) => setDonationDraft({ ...donationDraft, anonymous: event.target.checked })} /> Show this contribution as anonymous</label>
          <button className="primary-action" type="submit" disabled={!campaign}><HeartPulse size={18} /> Pledge donation</button>
          <p className="consent-copy">Online collection opens only when an approved payment URL is configured; otherwise this records a traceable pledge for manual confirmation.</p>
        </form>
      </section>

      {(canHandleWelfare || canHandleSupplies || canSeeHospitalPrep) && (
        <section className="hub-grid hub-grid-3">
          {canHandleWelfare && <ResponseCaseList title="Family welfare checks" eyebrow="Call responder queue" items={hub.welfare_checks || []} empty="No family checks waiting." onAdvance={onWelfareAdvance} primary="relative_name" secondary="last_known_location" />}
          {canHandleSupplies && (
            <ResponseCaseList
              title="Food and supply requests"
              eyebrow="Relief delivery queue"
              items={hub.supply_requests || []}
              empty="No supply requests waiting."
              onAdvance={onSupplyAdvance}
              primary="description"
              secondary="assigned_unit"
              assignmentOptions={(hub.responder_units || [])
                .filter((item) => item.availability_status === 'available')
                .map((item) => ({ label: `${item.name} · ${item.unit_type}`, value: item.name }))}
            />
          )}
          {canSeeHospitalPrep && (
            <section className="panel hub-panel">
              <PanelTitle eyebrow="Incoming patient early warning" title="Hospital preparation alerts" />
              <div className="hub-feed">
                {(hub.hospital_notifications || []).map((item) => (
                  <article className="hub-feed-item" key={item.id}>
                    <div className="hub-item-heading">
                      <div><strong>{item.expected_patients} incoming patient{item.expected_patients === 1 ? '' : 's'}</strong><span>Priority {item.priority} · rescue #{item.rescue_request_id}</span></div>
                      <StatusPill value={item.status} />
                    </div>
                    <p>{item.message}</p>
                    {canAcknowledgeHospitalPrep && (
                      <button className="compact-button" type="button" disabled={item.status === 'acknowledged'} onClick={() => onHospitalAcknowledge(item)}>
                        {item.status === 'acknowledged' ? 'Preparation confirmed' : 'Acknowledge and prepare'}
                      </button>
                    )}
                    {!canAcknowledgeHospitalPrep && <small>Receiving-hospital acknowledgement is visible here when confirmed.</small>}
                  </article>
                ))}
                {!(hub.hospital_notifications || []).length && <EmptyState title="No incoming notices" detail="Automatic rescue allocation will notify the nearest hospital here." />}
              </div>
            </section>
          )}
        </section>
      )}

      {canHandleWelfare && (
        <section className="panel hub-panel">
          <PanelTitle eyebrow="Automatic proximity allocation" title="Professional rescue units, volunteers, and ambulances" />
          <div className="dispatch-audit-grid">
            {(hub.dispatches || []).slice(0, 12).map((item) => (
              <article className="hub-feed-item" key={item.id}>
                <div className="hub-item-heading"><div><strong>{item.responder_name}</strong><span>{item.responder_type.replace('_', ' ')} · rescue #{item.rescue_request_id}</span></div><StatusPill value={item.status} /></div>
                <p>{Number(item.distance_km).toFixed(1)} km from the reported device coordinates at allocation time.</p>
              </article>
            ))}
            {!(hub.dispatches || []).length && <EmptyState title="No automatic dispatches yet" detail="Creating a rescue request reserves the nearest available professional unit, volunteer, and required ambulance." />}
          </div>
        </section>
      )}

      {canPublishNews && (
        <section className="panel form-panel news-publisher">
          <PanelTitle eyebrow="Authorized publishing" title="Post a verified field update or live stream" />
          <form className="news-publisher-form" onSubmit={onNewsSubmit}>
            <Select label="Disaster" value={newsDraft.disaster_id} options={disasters.map((item) => ({ label: item.title, value: item.id }))} onChange={(value) => setNewsDraft({ ...newsDraft, disaster_id: value })} />
            <Input label="Headline" value={newsDraft.headline} onChange={(value) => setNewsDraft({ ...newsDraft, headline: value })} required />
            <Input label="Verified source" value={newsDraft.source_name} onChange={(value) => setNewsDraft({ ...newsDraft, source_name: value })} required />
            <div className="form-row form-row-2"><Input label="State" value={newsDraft.state} onChange={(value) => setNewsDraft({ ...newsDraft, state: value })} required /><Input label="District" value={newsDraft.district} onChange={(value) => setNewsDraft({ ...newsDraft, district: value })} required /></div>
            <Textarea label="Situation update" value={newsDraft.summary} onChange={(value) => setNewsDraft({ ...newsDraft, summary: value })} required />
            <Input label="Livestream URL (optional)" type="url" value={newsDraft.stream_url} onChange={(value) => setNewsDraft({ ...newsDraft, stream_url: value })} />
            <label className="toggle-row"><input type="checkbox" checked={newsDraft.is_live} onChange={(event) => setNewsDraft({ ...newsDraft, is_live: event.target.checked })} /> Mark source as live now</label>
            <button className="primary-action" type="submit"><Send size={18} /> Publish verified update</button>
          </form>
        </section>
      )}
    </section>
  );
}

function ResponseCaseList({ title, eyebrow, items, empty, onAdvance, primary, secondary, assignmentOptions = null }) {
  const [selectedAssignments, setSelectedAssignments] = useState({});
  const usesRegisteredAssignments = Array.isArray(assignmentOptions);
  return (
    <section className="panel hub-panel">
      <PanelTitle eyebrow={eyebrow} title={title} />
      <div className="hub-feed">
        {items.map((item) => {
          const needsAssignment = usesRegisteredAssignments && item.status === 'requested' && !item.assigned_unit;
          const selectedAssignment = selectedAssignments[item.id] || '';
          return (
            <article className="hub-feed-item" key={item.id}>
              <div className="hub-item-heading"><div><strong>{item[primary]}</strong><span>{item[secondary] || `Case #${item.id}`}</span></div><StatusPill value={item.status} /></div>
              {item.responder_notes && <p>{item.responder_notes}</p>}
              {needsAssignment && (
                <>
                  <Select
                    label="Verified response unit"
                    value={selectedAssignment}
                    options={[
                      { label: 'Choose an available unit', value: '' },
                      ...assignmentOptions,
                    ]}
                    onChange={(value) => setSelectedAssignments((current) => ({ ...current, [item.id]: value }))}
                  />
                  {!assignmentOptions.length && <small>No registered response units are currently available.</small>}
                </>
              )}
              <button
                className="compact-button"
                type="button"
                disabled={['closed', 'delivered'].includes(item.status) || (needsAssignment && !selectedAssignment)}
                onClick={() => onAdvance(item, selectedAssignment)}
              >
                Advance response
              </button>
            </article>
          );
        })}
        {!items.length && <EmptyState title="Queue clear" detail={empty} />}
      </div>
    </section>
  );
}

function PhoneCallIcon() {
  return <span aria-hidden="true">☎</span>;
}

function formatCurrency(value, currency = 'INR') {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency, maximumFractionDigits: 0 }).format(value || 0);
}

function formatDateTime(value) {
  if (!value) return 'unknown';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return String(value);
  return parsed.toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' });
}

function FacilitiesView({ role, facilities, updateHospital, updateShelter, updateAmbulanceStatus }) {
  const showHospitals = ['Admin', 'Hospital', 'Ambulance', 'Police', 'Fire Service'].includes(role);
  const showShelters = ['Admin', 'Shelter', 'NGO', 'Citizen', 'Volunteer'].includes(role);
  const showAmbulances = ['Admin', 'Ambulance', 'Police', 'Fire Service'].includes(role);

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
                {['Admin', 'Hospital'].includes(role) && (
                  <div className="stepper">
                    <button type="button" onClick={() => updateHospital(item.id, -5)}>-</button>
                    <strong>{item.available_beds}</strong>
                    <button type="button" onClick={() => updateHospital(item.id, 5)}>+</button>
                  </div>
                )}
              </div>
            ))}
            {!facilities.hospitals.length && <p className="muted-copy">No hospital is assigned to this account. Ask an administrator to complete the facility assignment.</p>}
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
                {['Admin', 'Shelter'].includes(role) && (
                  <div className="stepper">
                    <button type="button" onClick={() => updateShelter(item.id, -10)}>-</button>
                    <strong>{item.available_capacity}</strong>
                    <button type="button" onClick={() => updateShelter(item.id, 10)}>+</button>
                  </div>
                )}
              </div>
            ))}
            {!facilities.shelters.length && <p className="muted-copy">No shelter is assigned to this account. Ask an administrator to complete the facility assignment.</p>}
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
                <div className="facility-actions">
                  <StatusPill value={item.status} />
                  {['Admin', 'Ambulance'].includes(role) && (
                    <button type="button" className="compact-button secondary-button" onClick={() => updateAmbulanceStatus(item.id)}>
                      Next status
                    </button>
                  )}
                </div>
              </div>
            ))}
            {!facilities.ambulances.length && <p className="muted-copy">No ambulance is assigned to this account. Ask an administrator to complete the vehicle assignment.</p>}
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

function Input({ label, value, onChange, type = 'text', required = false, step, minLength, autoComplete, inputMode }) {
  return (
    <label className="form-field">
      <span>{label}</span>
      <input className="form-control" type={type} step={step} minLength={minLength} autoComplete={autoComplete} inputMode={inputMode} value={value} required={required} onChange={(event) => onChange(event.target.value)} />
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
