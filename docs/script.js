/* ============================================
   GRIDGUARD — frontend logic
   Runs across all pages (login, dashboard/overview, alerts, sensors).
   Each section checks whether its relevant elements exist on the current
   page before doing anything, so one file can safely serve every page.
   ============================================ */

const TOKEN_KEY = 'gridguard_token';

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}
function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}
function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = options.headers || {};
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });

  if (res.status === 401) {
    clearToken();
    window.location.href = 'index.html';
    throw new Error('Not authenticated');
  }
  return res;
}

/* ============================================
   LOGIN / REGISTER PAGE (index.html)
   ============================================ */

const loginForm = document.getElementById('login-form');
if (loginForm) {
  if (getToken()) window.location.href = 'dashboard.html';

  const loginBtn = document.getElementById('login-submit-btn');

  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const errorEl = document.getElementById('login-error');

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    const body = new URLSearchParams();
    body.append('username', email);
    body.append('password', password);

    loginBtn.disabled = true;
    loginBtn.textContent = 'Logging in…';
    errorEl.style.color = 'var(--text-dim)';
    errorEl.textContent = 'Connecting — this can take up to a minute if the server has been idle.';

    try {
      const res = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body,
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || 'Login failed');
      }
      const data = await res.json();
      errorEl.textContent = '';
      setToken(data.access_token);
      window.location.href = 'dashboard.html';
    } catch (err) {
      errorEl.style.color = 'var(--red)';
      errorEl.textContent = err.message;
      loginBtn.disabled = false;
      loginBtn.textContent = 'Log in';
    }
  });
}

const registerForm = document.getElementById('register-form');
if (registerForm) {
  const registerBtn = document.getElementById('register-submit-btn');

  registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const errorEl = document.getElementById('register-error');

    const payload = {
      full_name: document.getElementById('reg-name').value,
      email: document.getElementById('reg-email').value,
      password: document.getElementById('reg-password').value,
    };

    registerBtn.disabled = true;
    registerBtn.textContent = 'Creating account…';
    errorEl.style.color = 'var(--text-dim)';
    errorEl.textContent = 'Connecting — this can take up to a minute if the server has been idle.';

    try {
      const res = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || 'Registration failed');
      }
      errorEl.style.color = 'var(--green)';
      errorEl.textContent = 'Account created — you can log in now.';
      registerForm.reset();
    } catch (err) {
      errorEl.style.color = 'var(--red)';
      errorEl.textContent = err.message;
    } finally {
      registerBtn.disabled = false;
      registerBtn.textContent = 'Create account';
    }
  });
}

/* ============================================
   SHARED APP SHELL (every page with a top nav)
   ============================================ */

const topbar = document.querySelector('.topbar');

let refreshAlertsPage = null;
let refreshDashboardOnAlert = null;

if (topbar) {
  if (!getToken()) {
    window.location.href = 'index.html';
  }

  const currentPage = document.body.dataset.page;
  document.querySelectorAll('.nav-link').forEach((link) => {
    if (link.dataset.page === currentPage) link.classList.add('active');
  });

  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
      clearToken();
      window.location.href = 'index.html';
    });
  }

  async function loadNavAlertBadge() {
    try {
      const res = await apiFetch('/alerts?resolved=false');
      const alerts = await res.json();
      const badge = document.getElementById('nav-alert-badge');
      if (badge) badge.textContent = alerts.length > 0 ? alerts.length : '';
    } catch {
    }
  }
  loadNavAlertBadge();

  const connectionStatus = document.getElementById('connection-status');

  function setConnectionStatus(state) {
    if (!connectionStatus) return;
    connectionStatus.classList.remove('connected', 'disconnected');
    if (state === 'connected') {
      connectionStatus.classList.add('connected');
      connectionStatus.innerHTML = '<span class="dot"></span> Live';
    } else {
      connectionStatus.classList.add('disconnected');
      connectionStatus.innerHTML = '<span class="dot"></span> Disconnected';
    }
  }

  function connectSensorFeed() {
    const ws = new WebSocket(`${WS_BASE_URL}/ws/sensors`);

    ws.onopen = () => setConnectionStatus('connected');
    ws.onclose = () => {
      setConnectionStatus('disconnected');
      setTimeout(connectSensorFeed, 3000);
    };
    ws.onerror = () => ws.close();

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'sensor_event') {
        const sensorFeed = document.getElementById('sensor-feed');
        if (!sensorFeed) return;

        const emptyState = sensorFeed.querySelector('.empty-state');
        if (emptyState) emptyState.remove();

        const li = document.createElement('li');
        li.className = `status-${data.status}`;
        const label = data.status === 'tamper_suspected' ? 'Tamper suspected' : 'Normal';
        li.innerHTML = `<span class="status-dot"></span> ${data.meter_number} — ${label}`;
        sensorFeed.prepend(li);

        while (sensorFeed.children.length > 30) {
          sensorFeed.removeChild(sensorFeed.lastChild);
        }
      }

      if (data.type === 'new_alert') {
        loadNavAlertBadge();
        if (refreshAlertsPage) refreshAlertsPage();
        if (refreshDashboardOnAlert) refreshDashboardOnAlert();
      }
    };
  }
  connectSensorFeed();
}

/* ============================================
   OVERVIEW / DASHBOARD PAGE (dashboard.html)
   ============================================ */

const householdsBody = document.getElementById('households-body');

if (householdsBody) {
  const addHouseholdBtn = document.getElementById('add-household-btn');
  const householdModal = document.getElementById('household-modal');
  const householdForm = document.getElementById('household-form');
  const cancelHouseholdBtn = document.getElementById('cancel-household');
  const householdSelect = document.getElementById('household-select');
  const recordForm = document.getElementById('record-form');
  const householdSearch = document.getElementById('household-search');

  let households = [];
  let selectedHouseholdId = null;
  let chart = null;
  let currentSearchTerm = '';
  let latestRisks = {};

  function riskBadge(score) {
    if (score === null || score === undefined) {
      return '<span class="risk-badge risk-none">—</span>';
    }
    let cls = 'risk-low';
    if (score >= 0.6) cls = 'risk-high';
    else if (score >= 0.3) cls = 'risk-medium';
    return `<span class="risk-badge ${cls}">${(score * 100).toFixed(0)}%</span>`;
  }

  function matchesSearch(h) {
    if (!currentSearchTerm) return true;
    const term = currentSearchTerm.toLowerCase();
    return (
      h.address.toLowerCase().includes(term) ||
      h.meter_number.toLowerCase().includes(term) ||
      (h.ward || '').toLowerCase().includes(term)
    );
  }

  function riskBadgeFor(id) {
    const risk = latestRisks[id];
    return riskBadge(risk ? risk.risk_score : null);
  }

  function renderHouseholdsTable() {
    const filtered = households.filter(matchesSearch);

    if (filtered.length === 0) {
      householdsBody.innerHTML = households.length === 0
        ? '<tr><td colspan="5">No households yet — add one to get started.</td></tr>'
        : '<tr><td colspan="5">No households match your search.</td></tr>';
      return;
    }

    householdsBody.innerHTML = filtered
      .map((h) => `
        <tr>
          <td>${h.meter_number}</td>
          <td>${h.address}</td>
          <td>${h.ward || '—'}</td>
          <td>${riskBadgeFor(h.id)}</td>
          <td><button class="view-household" data-id="${h.id}">View</button></td>
        </tr>
      `)
      .join('');

    document.querySelectorAll('.view-household').forEach((btn) => {
      btn.addEventListener('click', () => {
        householdSelect.value = btn.dataset.id;
        selectHousehold(btn.dataset.id);
      });
    });
  }

  async function loadHouseholds() {
    const res = await apiFetch('/households');
    households = await res.json();

    householdSelect.innerHTML =
      '<option value="">Select a household</option>' +
      households.map((h) => `<option value="${h.id}">${h.meter_number} — ${h.address}</option>`).join('');

    if (households.length === 0) {
      renderHouseholdsTable();
      return;
    }

    const risks = await Promise.all(
      households.map((h) =>
        apiFetch(`/households/${h.id}/risk`)
          .then((r) => (r.ok ? r.json() : null))
          .catch(() => null)
      )
    );
    latestRisks = {};
    households.forEach((h, i) => { latestRisks[h.id] = risks[i]; });

    renderHouseholdsTable();
  }
  refreshDashboardOnAlert = loadHouseholds;

  if (householdSearch) {
    householdSearch.addEventListener('input', () => {
      currentSearchTerm = householdSearch.value.trim();
      renderHouseholdsTable();
    });
  }

  addHouseholdBtn.addEventListener('click', () => {
    householdModal.classList.add('active');
  });
  cancelHouseholdBtn.addEventListener('click', () => {
    householdModal.classList.remove('active');
  });
  householdModal.addEventListener('click', (e) => {
    if (e.target === householdModal) householdModal.classList.remove('active');
  });

  householdForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      meter_number: document.getElementById('hh-meter').value,
      address: document.getElementById('hh-address').value,
      ward: document.getElementById('hh-ward').value || null,
    };
    const res = await apiFetch('/households', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (res.ok) {
      householdModal.classList.remove('active');
      householdForm.reset();
      await loadHouseholds();
    } else {
      const data = await res.json().catch(() => ({}));
      alert(data.detail || 'Could not add household');
    }
  });

  householdSelect.addEventListener('change', () => selectHousehold(householdSelect.value));

  async function selectHousehold(id) {
    selectedHouseholdId = id || null;
    if (!selectedHouseholdId) {
      if (chart) chart.destroy();
      return;
    }
    const res = await apiFetch(`/households/${selectedHouseholdId}/consumption`);
    const records = await res.json();
    renderChart(records);
  }

  function renderChart(records) {
    const ctx = document.getElementById('consumption-chart');
    const labels = records.map((r) => r.month);
    const purchases = records.map((r) => r.purchase_rand);
    const consumption = records.map((r) => r.consumption_kwh);

    if (chart) chart.destroy();
    chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label: 'Purchase (R)',
            data: purchases,
            borderColor: '#FFC300',
            backgroundColor: 'rgba(255,195,0,0.1)',
            tension: 0.3,
          },
          {
            label: 'Consumption (kWh)',
            data: consumption,
            borderColor: '#7C5CFF',
            backgroundColor: 'rgba(124,92,255,0.1)',
            tension: 0.3,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: { legend: { labels: { color: '#080807' } } },
        scales: {
          x: { ticks: { color: '#8D8A99' }, grid: { color: '#2E2E3A' } },
          y: { ticks: { color: '#8D8A99' }, grid: { color: '#2E2E3A' } },
        },
      },
    });
  }

  recordForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!selectedHouseholdId) {
      alert('Select a household first.');
      return;
    }
    const payload = {
      month: document.getElementById('record-month').value,
      purchase_rand: parseFloat(document.getElementById('record-purchase').value),
      consumption_kwh: parseFloat(document.getElementById('record-consumption').value),
    };
    const res = await apiFetch(`/households/${selectedHouseholdId}/consumption`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (res.ok) {
      recordForm.reset();
      await selectHousehold(selectedHouseholdId);
      await loadHouseholds();
    } else {
      const data = await res.json().catch(() => ({}));
      alert(data.detail || 'Could not log record');
    }
  });

  loadHouseholds();
}

/* ============================================
   ALERTS PAGE (alerts.html)
   ============================================ */

const alertsList = document.getElementById('alerts-list');

if (alertsList) {
  const alertCount = document.getElementById('alert-count');
  const filterButtons = document.querySelectorAll('.filter-btn');
  let currentFilter = 'false'; // 'false' = open, 'true' = resolved, '' = all

  function renderAlert(a) {
    const li = document.createElement('li');
    li.className = `severity-${a.severity}`;
    li.dataset.id = a.id;
    li.innerHTML = `
      <div>${a.message}</div>
      <div class="alert-meta">
        <span>${new Date(a.created_at).toLocaleString()}</span>
        ${a.resolved ? '<span>resolved</span>' : `<button class="resolve-btn" data-id="${a.id}">Resolve</button>`}
      </div>
    `;
    return li;
  }

  async function loadAlerts() {
    const query = currentFilter === '' ? '' : `?resolved=${currentFilter}`;
    const res = await apiFetch(`/alerts${query}`);
    const alerts = await res.json();

    alertCount.textContent = alerts.length;
    alertsList.innerHTML = '';

    if (alerts.length === 0) {
      alertsList.innerHTML = '<li class="empty-state">No alerts in this view.</li>';
      return;
    }

    alerts.forEach((a) => alertsList.appendChild(renderAlert(a)));
    attachResolveHandlers();
  }
  refreshAlertsPage = loadAlerts;

  function attachResolveHandlers() {
    document.querySelectorAll('.resolve-btn').forEach((btn) => {
      btn.addEventListener('click', async () => {
        const id = btn.dataset.id;
        const res = await apiFetch(`/alerts/${id}/resolve`, { method: 'POST' });
        if (res.ok) {
          await loadAlerts();
        }
      });
    });
  }

  filterButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      filterButtons.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      currentFilter = btn.dataset.filter;
      loadAlerts();
    });
  });

  loadAlerts();
}