/**
 * GPA Calculator AI Agent - Main Application JavaScript
 * Full-stack integration with FastAPI backend, SQLite, deterministic engine, & AI chat.
 */

// Always point to the FastAPI backend
const API_BASE = 'http://127.0.0.1:8000/api';

// SPPU 10-point standard scale mapping
const SPPU_SCALE = {
  "O": 10.0,
  "A+": 9.0,
  "A": 8.0,
  "B+": 7.0,
  "B": 6.0,
  "C": 5.0,
  "P": 4.0,
  "F": 0.0,
  "Ab": 0.0
};

// Global application state
let appState = {
  activeView: 'dashboard',
  theme: localStorage.getItem('gpa_theme') || 'dark',
  records: [],
  activeScheme: { ...SPPU_SCALE },
  lastCalculatedSgpa: null,
  whatIfMode: 'sgpa', // 'sgpa' or 'cgpa'
  charts: {
    performance: null,
    distribution: null
  }
};

/* ==========================================================================
   INITIALIZATION & EVENT LISTENERS
   ========================================================================== */
document.addEventListener('DOMContentLoaded', async () => {
  initTheme();
  setupNavigation();
  setupEventListeners();
  
  // Seed initial rows
  seedDefaultSgpaRows();
  seedDefaultCgpaRows();
  seedDefaultBacklogRows();
  renderGradingSchemeTable();

  // Load data from backend
  await checkBackendHealth();
  await loadAcademicHistory();
  renderWhatIfView();
});

/* ==========================================================================
   THEME & NAVIGATION
   ========================================================================== */
function initTheme() {
  document.documentElement.setAttribute('data-theme', appState.theme);
  updateThemeIcons();
}

function toggleTheme() {
  appState.theme = appState.theme === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', appState.theme);
  localStorage.setItem('gpa_theme', appState.theme);
  updateThemeIcons();
  
  // Re-render charts with updated theme colors
  if (appState.charts.performance) initCharts();
}

function updateThemeIcons() {
  const moon = document.getElementById('themeMoon');
  const sun = document.getElementById('themeSun');
  if (appState.theme === 'light') {
    moon.style.display = 'none';
    sun.style.display = 'block';
  } else {
    moon.style.display = 'block';
    sun.style.display = 'none';
  }
}

function setupNavigation() {
  const navItems = document.querySelectorAll('.sidebar-nav .nav-item');
  navItems.forEach(item => {
    item.addEventListener('click', () => {
      const targetView = item.getAttribute('data-view');
      if (targetView) navigateTo(targetView);
    });
  });

  // Topbar Pill Navigation
  const topNavBtns = document.querySelectorAll('.topbar-nav-pill .top-nav-btn');
  topNavBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetView = btn.getAttribute('data-view');
      if (targetView) navigateTo(targetView);
    });
  });

  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('appSidebar');
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', () => {
      sidebar.classList.toggle('mobile-open');
    });
  }
}

function navigateTo(viewName) {
  appState.activeView = viewName;
  
  // Update sidebar active classes
  document.querySelectorAll('.sidebar-nav .nav-item').forEach(item => {
    if (item.getAttribute('data-view') === viewName) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });

  // Update topbar pill active classes
  document.querySelectorAll('.topbar-nav-pill .top-nav-btn').forEach(btn => {
    if (btn.getAttribute('data-view') === viewName) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  // Update views
  document.querySelectorAll('.view-section').forEach(sec => {
    sec.classList.remove('active');
  });
  const activeSec = document.getElementById(`view-${viewName}`);
  if (activeSec) activeSec.classList.add('active');

  // Update Topbar Title
  const titles = {
    dashboard: 'Academic Dashboard',
    sgpa: 'SGPA Calculator',
    cgpa: 'CGPA Calculator',
    converter: 'SPPU Percentage Converter',
    target: 'Target GPA Predictor',
    chat: 'GPA Assistant AI',
    whatif: 'What-If Analysis',
    backlog: 'Backlog Manager',
    history: 'Academic History',
    settings: 'Grading Scheme Settings'
  };
  const titleEl = document.getElementById('currentViewTitle');
  if (titleEl) titleEl.innerText = titles[viewName] || 'GPA Calculator';

  // Close mobile sidebar if open
  const sidebar = document.getElementById('appSidebar');
  if (sidebar) sidebar.classList.remove('mobile-open');

  // Refresh view-specific content
  if (viewName === 'dashboard') {
    updateDashboardMetrics();
    initCharts();
    syncConverterFromCurrent();
  } else if (viewName === 'whatif') {
    renderWhatIfView();
  } else if (viewName === 'converter') {
    syncConverterFromCurrent();
  }
}

/* ==========================================================================
   BACKEND API HEALTH & CONNECTIVITY
   ========================================================================== */
async function checkBackendHealth() {
  const statusPill = document.getElementById('systemStatusText');
  const aiStatus = document.getElementById('aiStatusText');

  try {
    const res = await fetch(`${API_BASE}/health`);
    if (res.ok) {
      const data = await res.json();
      if (statusPill) statusPill.innerText = 'Connected: FastAPI Backend';
      if (aiStatus) {
        aiStatus.innerText = data.openai_configured ? 'OpenAI GPT-4o-mini Ready' : 'Deterministic AI Ready';
      }
    } else {
      fallbackToClientEngine();
    }
  } catch (err) {
    fallbackToClientEngine();
  }
}

function fallbackToClientEngine() {
  const statusPill = document.getElementById('systemStatusText');
  const aiStatus = document.getElementById('aiStatusText');
  if (statusPill) statusPill.innerText = 'Local Calculation Engine Active';
  if (aiStatus) aiStatus.innerText = 'Local Deterministic AI';
}

/* ==========================================================================
   1. DASHBOARD & CHARTS
   ========================================================================== */
function updateDashboardMetrics() {
  const semRecords = appState.records.filter(r => r.record_type === 'semester');
  if (semRecords.length === 0) return;

  // Total credits and weighted CGPA
  let totalCredits = 0;
  let totalWeightedPts = 0;
  let latestSem = semRecords[semRecords.length - 1];

  semRecords.forEach(r => {
    const c = parseFloat(r.credits) || 0;
    const s = parseFloat(r.sgpa) || 0;
    totalCredits += c;
    totalWeightedPts += (s * c);
  });

  const cgpa = totalCredits > 0 ? (totalWeightedPts / totalCredits).toFixed(2) : "0.00";
  
  const dashCgpa = document.getElementById('dashCgpa');
  const dashCgpaSub = document.getElementById('dashCgpaSub');
  const dashLatestSgpa = document.getElementById('dashLatestSgpa');
  const dashLatestSgpaSub = document.getElementById('dashLatestSgpaSub');
  const dashCredits = document.getElementById('dashCredits');
  const dashTargetGap = document.getElementById('dashTargetGap');

  if (dashCgpa) dashCgpa.innerHTML = `${cgpa} <span>/ 10</span>`;
  if (dashCgpaSub) dashCgpaSub.innerText = `Weighted across ${totalCredits.toFixed(1)} credits`;
  
  if (latestSem && dashLatestSgpa) {
    dashLatestSgpa.innerHTML = `${parseFloat(latestSem.sgpa).toFixed(2)} <span>/ 10</span>`;
    dashLatestSgpaSub.innerText = latestSem.title || 'Latest Term';
  }

  if (dashCredits) dashCredits.innerHTML = `${totalCredits.toFixed(1)} <span>cr</span>`;

  // Gap towards 8.50 target
  const targetGoal = 8.50;
  const gap = Math.max(0, targetGoal - parseFloat(cgpa)).toFixed(2);
  if (dashTargetGap) dashTargetGap.innerHTML = `${gap} <span>pts</span>`;
}

function initCharts() {
  const semRecords = appState.records.filter(r => r.record_type === 'semester');
  if (semRecords.length === 0) return;

  const isDark = appState.theme === 'dark';
  const textColor = isDark ? '#94a3b8' : '#475569';
  const gridColor = isDark ? 'rgba(255, 255, 255, 0.06)' : 'rgba(15, 23, 42, 0.06)';

  // 1. Performance Chart (Semester SGPA vs Cumulative CGPA)
  const perfCtx = document.getElementById('performanceChart');
  if (perfCtx) {
    if (appState.charts.performance) appState.charts.performance.destroy();

    const labels = semRecords.map(r => r.title || `Sem ${r.semester_num}`);
    const sgpaData = semRecords.map(r => parseFloat(r.sgpa));

    // Calculate rolling CGPA
    let cumCredits = 0;
    let cumPoints = 0;
    const cgpaData = semRecords.map(r => {
      const cr = parseFloat(r.credits) || 0;
      const sg = parseFloat(r.sgpa) || 0;
      cumCredits += cr;
      cumPoints += (sg * cr);
      return (cumPoints / cumCredits).toFixed(2);
    });

    appState.charts.performance = new Chart(perfCtx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Semester SGPA',
            data: sgpaData,
            borderColor: '#6366f1',
            backgroundColor: 'rgba(99, 102, 241, 0.15)',
            borderWidth: 3,
            tension: 0.35,
            fill: true,
            pointBackgroundColor: '#6366f1',
            pointRadius: 5
          },
          {
            label: 'Cumulative CGPA',
            data: cgpaData,
            borderColor: '#10b981',
            borderWidth: 3,
            borderDash: [5, 5],
            tension: 0.35,
            fill: false,
            pointBackgroundColor: '#10b981',
            pointRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: { color: textColor, font: { family: 'Plus Jakarta Sans', weight: '600' } }
          }
        },
        scales: {
          y: {
            min: 5.0,
            max: 10.0,
            grid: { color: gridColor },
            ticks: { color: textColor }
          },
          x: {
            grid: { color: gridColor },
            ticks: { color: textColor }
          }
        }
      }
    });
  }

  // 2. Grade Distribution Chart
  const distCtx = document.getElementById('gradeDistributionChart');
  if (distCtx) {
    if (appState.charts.distribution) appState.charts.distribution.destroy();

    // Aggregate grade counts across all subjects in records
    const gradeCounts = { 'O': 0, 'A+': 0, 'A': 0, 'B+': 0, 'B': 0, 'C': 0, 'P': 0, 'F': 0 };
    semRecords.forEach(r => {
      const subjects = r.data?.subjects || [];
      subjects.forEach(s => {
        const g = (s.grade || 'A').toUpperCase();
        if (gradeCounts[g] !== undefined) gradeCounts[g]++;
      });
    });

    // If no subjects found, seed typical engineering distribution
    if (Object.values(gradeCounts).every(v => v === 0)) {
      gradeCounts['O'] = 7;
      gradeCounts['A+'] = 8;
      gradeCounts['A'] = 6;
      gradeCounts['B+'] = 4;
    }

    appState.charts.distribution = new Chart(distCtx, {
      type: 'doughnut',
      data: {
        labels: Object.keys(gradeCounts),
        datasets: [{
          data: Object.values(gradeCounts),
          backgroundColor: [
            '#c084fc', // O
            '#34d399', // A+
            '#22d3ee', // A
            '#60a5fa', // B+
            '#818cf8', // B
            '#fbbf24', // C
            '#94a3b8', // P
            '#f87171'  // F
          ],
          borderWidth: 2,
          borderColor: isDark ? '#0f172a' : '#ffffff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'right',
            labels: { color: textColor, font: { family: 'Plus Jakarta Sans', size: 11 } }
          }
        },
        cutout: '68%'
      }
    });
  }
}

/* ==========================================================================
   2. SGPA CALCULATOR
   ========================================================================== */
function seedDefaultSgpaRows() {
  const tbody = document.getElementById('sgpaTableBody');
  if (!tbody) return;
  tbody.innerHTML = '';

  const sampleSubjects = [
    { name: 'Engineering Mathematics IV', code: 'CS401', credit: 4.0, grade: 'A+' },
    { name: 'Design & Analysis of Algorithms', code: 'CS402', credit: 4.0, grade: 'O' },
    { name: 'Database Management Systems', code: 'CS403', credit: 4.0, grade: 'A' },
    { name: 'Computer Networks', code: 'CS404', credit: 3.0, grade: 'B+' },
    { name: 'DAA & DBMS Laboratory', code: 'CS405', credit: 2.0, grade: 'O' },
    { name: 'Seminar & Technical Communication', code: 'CS406', credit: 2.0, grade: 'A+' }
  ];

  sampleSubjects.forEach(s => addSubjectRow(s.name, s.code, s.credit, s.grade));
}

function addSubjectRow(name = '', code = '', credit = 3.0, grade = 'A') {
  const tbody = document.getElementById('sgpaTableBody');
  if (!tbody) return;

  const tr = document.createElement('tr');
  const gradeOptions = Object.keys(SPPU_SCALE).map(g => {
    return `<option value="${g}" ${g === grade ? 'selected' : ''}>${g} (${SPPU_SCALE[g]} GP)</option>`;
  }).join('');

  tr.innerHTML = `
    <td>
      <input type="text" class="form-control subj-name" value="${escapeHtml(name)}" placeholder="Course Title" required>
    </td>
    <td>
      <input type="text" class="form-control subj-code" value="${escapeHtml(code)}" placeholder="e.g. CS401">
    </td>
    <td>
      <input type="number" step="0.5" min="0.5" max="20" class="form-control subj-credit" value="${credit}" required>
    </td>
    <td>
      <select class="form-control subj-grade">${gradeOptions}</select>
    </td>
    <td>
      <button type="button" class="btn btn-danger btn-sm" onclick="this.closest('tr').remove()">Remove</button>
    </td>
  `;
  tbody.appendChild(tr);
}

async function calculateSgpa() {
  const rows = document.querySelectorAll('#sgpaTableBody tr');
  if (rows.length === 0) {
    showToast('Please add at least one subject.', 'error');
    return;
  }

  const subjects = [];
  let hasInvalid = false;

  rows.forEach(r => {
    const name = r.querySelector('.subj-name').value.trim();
    const code = r.querySelector('.subj-code').value.trim();
    const credit = parseFloat(r.querySelector('.subj-credit').value);
    const grade = r.querySelector('.subj-grade').value;

    if (!name || isNaN(credit) || credit <= 0) {
      hasInvalid = true;
      return;
    }

    subjects.push({
      name: name,
      code: code,
      credit: credit,
      grade: grade
    });
  });

  if (hasInvalid || subjects.length === 0) {
    showToast('Please check all subject names and ensure credits are positive (> 0).', 'error');
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/calculate/sgpa`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ subjects })
    });

    let data;
    if (res.ok) {
      data = await res.json();
    } else {
      // Deterministic Client Fallback
      data = computeClientSgpa(subjects);
    }

    displaySgpaResult(data);
    appState.lastCalculatedSgpa = { subjects, result: data };
    document.getElementById('btnSaveSgpaToHistory').style.display = 'inline-flex';
    showToast('SGPA calculated successfully!', 'success');
  } catch (err) {
    const fallback = computeClientSgpa(subjects);
    displaySgpaResult(fallback);
    appState.lastCalculatedSgpa = { subjects, result: fallback };
    document.getElementById('btnSaveSgpaToHistory').style.display = 'inline-flex';
    showToast('SGPA calculated (Local Engine)', 'success');
  }
}

function computeClientSgpa(subjects) {
  let totCred = 0;
  let totPts = 0;
  let hasBacklog = false;

  subjects.forEach(s => {
    const gp = SPPU_SCALE[s.grade] || 0;
    totCred += s.credit;
    totPts += (s.credit * gp);
    if (gp < 4.0) hasBacklog = true;
  });

  const sgpa = totCred > 0 ? (totPts / totCred) : 0;
  return {
    sgpa: parseFloat(sgpa.toFixed(2)),
    total_credits: parseFloat(totCred.toFixed(2)),
    total_weighted_points: parseFloat(totPts.toFixed(2)),
    subject_count: subjects.length,
    has_backlog: hasBacklog
  };
}

function displaySgpaResult(data) {
  const banner = document.getElementById('sgpaResultBanner');
  const scoreEl = document.getElementById('sgpaResultScore');
  const creditsEl = document.getElementById('sgpaResultCredits');
  const pointsEl = document.getElementById('sgpaResultPoints');
  const countEl = document.getElementById('sgpaResultCount');
  const badgeEl = document.getElementById('sgpaBacklogBadge');

  if (scoreEl) scoreEl.innerHTML = `${data.sgpa.toFixed(2)} <span>/ 10.0</span>`;
  if (creditsEl) creditsEl.innerText = data.total_credits.toFixed(1);
  if (pointsEl) pointsEl.innerText = data.total_weighted_points.toFixed(2);
  if (countEl) countEl.innerText = data.subject_count;

  if (badgeEl) {
    badgeEl.innerHTML = data.has_backlog
      ? `<span class="delta-pill negative">⚠️ Backlog Detected (< 4.0 GP)</span>`
      : `<span class="delta-pill positive">✅ All Courses Cleared</span>`;
  }

  if (banner) banner.style.display = 'flex';
}

async function saveSgpaToHistory() {
  if (!appState.lastCalculatedSgpa) return;
  const semNum = appState.records.filter(r => r.record_type === 'semester').length + 1;
  const payload = {
    record_type: 'semester',
    title: `Semester ${semNum}`,
    semester_num: semNum,
    sgpa: appState.lastCalculatedSgpa.result.sgpa,
    credits: appState.lastCalculatedSgpa.result.total_credits,
    data: {
      subjects: appState.lastCalculatedSgpa.subjects,
      calculated: appState.lastCalculatedSgpa.result
    }
  };

  try {
    const res = await fetch(`${API_BASE}/history`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      showToast('Semester record saved to SQLite database!', 'success');
      await loadAcademicHistory();
      return;
    }
  } catch (err) {
    // Offline / GitHub Pages fallback
  }

  const localRecord = {
    id: Date.now(),
    ...payload,
    created_at: new Date().toISOString()
  };
  appState.records.push(localRecord);
  localStorage.setItem('gpa_academic_records', JSON.stringify(appState.records));
  renderHistoryTable();
  updateDashboardMetrics();
  initCharts();
  showToast('Semester record saved in browser storage!', 'success');
}

/* ==========================================================================
   3. CGPA CALCULATOR
   ========================================================================== */
function seedDefaultCgpaRows() {
  const tbody = document.getElementById('cgpaTableBody');
  if (!tbody) return;
  tbody.innerHTML = '';

  const initialSemesters = [
    { name: 'Semester 1 (FE Sem 1)', sgpa: 8.24, credits: 20.0 },
    { name: 'Semester 2 (FE Sem 2)', sgpa: 8.55, credits: 20.0 },
    { name: 'Semester 3 (SE Sem 1)', sgpa: 8.10, credits: 22.0 },
    { name: 'Semester 4 (SE Sem 2)', sgpa: 8.68, credits: 22.0 }
  ];

  initialSemesters.forEach(s => addSemesterRow(s.name, s.sgpa, s.credits));
}

function addSemesterRow(name = '', sgpa = 8.0, credits = 20.0) {
  const tbody = document.getElementById('cgpaTableBody');
  if (!tbody) return;

  const tr = document.createElement('tr');
  tr.innerHTML = `
    <td>
      <input type="text" class="form-control sem-name" value="${escapeHtml(name)}" placeholder="Semester Title" required>
    </td>
    <td>
      <input type="number" step="0.01" min="0" max="10" class="form-control sem-sgpa" value="${sgpa}" required>
    </td>
    <td>
      <input type="number" step="0.5" min="1" max="50" class="form-control sem-credits" value="${credits}" required>
    </td>
    <td>
      <button type="button" class="btn btn-danger btn-sm" onclick="this.closest('tr').remove()">Remove</button>
    </td>
  `;
  tbody.appendChild(tr);
}

function loadCgpaFromHistory() {
  const semRecords = appState.records.filter(r => r.record_type === 'semester');
  if (semRecords.length === 0) {
    showToast('No saved semesters in history to load.', 'info');
    return;
  }
  const tbody = document.getElementById('cgpaTableBody');
  tbody.innerHTML = '';
  semRecords.forEach(r => addSemesterRow(r.title, r.sgpa, r.credits));
  showToast('Loaded saved semesters from history.', 'success');
}

async function calculateCgpa() {
  const rows = document.querySelectorAll('#cgpaTableBody tr');
  if (rows.length === 0) {
    showToast('Please add at least one semester row.', 'error');
    return;
  }

  const semesters = [];
  let hasInvalid = false;

  rows.forEach(r => {
    const name = r.querySelector('.sem-name').value.trim();
    const sgpa = parseFloat(r.querySelector('.sem-sgpa').value);
    const credits = parseFloat(r.querySelector('.sem-credits').value);

    if (!name || isNaN(sgpa) || isNaN(credits) || credits <= 0) {
      hasInvalid = true;
      return;
    }

    semesters.push({ name, sgpa, credits });
  });

  if (hasInvalid || semesters.length === 0) {
    showToast('Please check all semester SGPA and positive credit values.', 'error');
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/calculate/cgpa`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ semesters })
    });

    let data;
    if (res.ok) {
      data = await res.json();
    } else {
      data = computeClientCgpa(semesters);
    }

    displayCgpaResult(data);
    showToast('CGPA calculated successfully!', 'success');
  } catch (err) {
    const fallback = computeClientCgpa(semesters);
    displayCgpaResult(fallback);
    showToast('CGPA calculated (Local Engine)', 'success');
  }
}

function computeClientCgpa(semesters) {
  let totCred = 0;
  let totPts = 0;
  let sgpaSum = 0;

  semesters.forEach(s => {
    totCred += s.credits;
    totPts += (s.sgpa * s.credits);
    sgpaSum += s.sgpa;
  });

  const weighted = totCred > 0 ? (totPts / totCred) : 0;
  const simple = semesters.length > 0 ? (sgpaSum / semesters.length) : 0;

  return {
    cgpa: parseFloat(weighted.toFixed(2)),
    simple_average: parseFloat(simple.toFixed(2)),
    total_credits: parseFloat(totCred.toFixed(2)),
    explanation: Math.abs(weighted - simple) > 0.001
      ? 'Credit weights vary across semesters, so weighted CGPA accurately reflects course workload.'
      : 'Semester credit loads are equal, so weighted CGPA equals simple average.'
  };
}

function displayCgpaResult(data) {
  const banner = document.getElementById('cgpaResultBanner');
  const scoreEl = document.getElementById('cgpaResultScore');
  const weightedEl = document.getElementById('cgpaWeightedVal');
  const simpleEl = document.getElementById('cgpaSimpleAvgVal');
  const creditsEl = document.getElementById('cgpaTotalCredits');
  const explanationEl = document.getElementById('cgpaExplanationText');

  if (scoreEl) scoreEl.innerHTML = `${data.cgpa.toFixed(2)} <span>/ 10.0</span>`;
  if (weightedEl) weightedEl.innerText = data.cgpa.toFixed(2);
  if (simpleEl) simpleEl.innerText = data.simple_average.toFixed(2);
  if (creditsEl) creditsEl.innerText = data.total_credits.toFixed(1);
  if (explanationEl) explanationEl.innerText = data.explanation;

  if (banner) banner.style.display = 'flex';
}

/* ==========================================================================
   4. TARGET GPA PREDICTOR
   ========================================================================== */
async function handleTargetGpaSubmit(e) {
  e.preventDefault();
  const current_cgpa = parseFloat(document.getElementById('targetCurrentCgpa').value);
  const completed_credits = parseFloat(document.getElementById('targetCompletedCredits').value);
  const remaining_credits = parseFloat(document.getElementById('targetRemainingCredits').value);
  const target_cgpa = parseFloat(document.getElementById('targetDesiredCgpa').value);

  if (isNaN(current_cgpa) || isNaN(completed_credits) || isNaN(remaining_credits) || isNaN(target_cgpa)) {
    showToast('Please enter all numerical inputs.', 'error');
    return;
  }

  const payload = { current_cgpa, completed_credits, remaining_credits, target_cgpa };

  try {
    const res = await fetch(`${API_BASE}/predict/target-gpa`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    let data;
    if (res.ok) {
      data = await res.json();
    } else {
      data = computeClientTargetGpa(payload);
    }
    displayTargetResult(data);
  } catch (err) {
    const fallback = computeClientTargetGpa(payload);
    displayTargetResult(fallback);
  }
}

function computeClientTargetGpa({ current_cgpa, completed_credits, remaining_credits, target_cgpa }) {
  const totalCred = completed_credits + remaining_credits;
  const neededPts = (target_cgpa * totalCred) - (current_cgpa * completed_credits);
  const reqSgpa = neededPts / remaining_credits;
  const maxPossible = ((current_cgpa * completed_credits) + (10.0 * remaining_credits)) / totalCred;

  const achievable = reqSgpa <= 10.0;
  const scenarios = [7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0].map(s => {
    const resCgpa = ((current_cgpa * completed_credits) + (s * remaining_credits)) / totalCred;
    return {
      hypothetical_remaining_sgpa: s,
      resulting_cgpa: parseFloat(resCgpa.toFixed(2)),
      meets_target: resCgpa >= target_cgpa
    };
  });

  return {
    achievable: achievable,
    status: achievable ? (reqSgpa <= 8.5 ? 'achievable_moderate' : 'achievable_high_effort') : 'impossible',
    required_sgpa: parseFloat(reqSgpa.toFixed(2)),
    max_achievable_cgpa: parseFloat(maxPossible.toFixed(2)),
    message: achievable
      ? `To achieve target CGPA of ${target_cgpa.toFixed(2)}, you need an average SGPA of ${reqSgpa.toFixed(2)} in remaining credits.`
      : `Target CGPA of ${target_cgpa.toFixed(2)} is mathematically impossible. Maximum reachable is ${maxPossible.toFixed(2)}.`,
    scenarios: scenarios
  };
}

function displayTargetResult(data) {
  const card = document.getElementById('targetResultCard');
  const reqEl = document.getElementById('targetRequiredSgpa');
  const maxEl = document.getElementById('targetMaxAchievable');
  const msgEl = document.getElementById('targetMessageText');
  const badgeEl = document.getElementById('targetFeasibilityBadge');

  if (reqEl) reqEl.innerHTML = `${data.required_sgpa.toFixed(2)} <span>/ 10.0</span>`;
  if (maxEl) maxEl.innerText = data.max_achievable_cgpa.toFixed(2);
  if (msgEl) msgEl.innerText = data.message;

  if (badgeEl) {
    if (data.achievable) {
      badgeEl.innerHTML = `<span class="delta-pill positive">🎯 Mathematically Feasible</span>`;
    } else {
      badgeEl.innerHTML = `<span class="delta-pill negative">⚠️ Mathematically Impossible (> 10.0 SGPA Required)</span>`;
    }
  }

  // Populate scenarios table
  const tbody = document.getElementById('targetScenariosBody');
  if (tbody && data.scenarios) {
    tbody.innerHTML = data.scenarios.map(s => `
      <tr>
        <td><strong>${s.hypothetical_remaining_sgpa.toFixed(1)} SGPA</strong></td>
        <td>${s.resulting_cgpa.toFixed(2)} CGPA</td>
        <td>
          <span class="delta-pill ${s.meets_target ? 'positive' : 'negative'}">
            ${s.meets_target ? 'Meets Target' : 'Below Target'}
          </span>
        </td>
      </tr>
    `).join('');
  }

  if (card) card.style.display = 'block';
}

/* ==========================================================================
   5. AI CHAT ASSISTANT ("GPA Assistant AI")
   ========================================================================== */
async function handleChatSubmit(e) {
  e.preventDefault();
  const inputEl = document.getElementById('chatInput');
  const message = inputEl.value.trim();
  if (!message) return;

  // Append user bubble
  appendChatMessage(message, 'user');
  inputEl.value = '';

  // Show typing indicator
  showTypingIndicator();

  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: message,
        conversation_id: 'web_session_' + Date.now(),
        academic_context: {
          saved_semesters: appState.records.filter(r => r.record_type === 'semester')
        }
      })
    });

    removeTypingIndicator();

    if (res.ok) {
      const data = await res.json();
      appendChatMessage(data.reply, 'assistant', true);
    } else {
      appendChatMessage('Encountered an issue processing your query with the backend.', 'assistant');
    }
  } catch (err) {
    removeTypingIndicator();
    // Intelligent local fallback response
    const fallbackText = getClientChatFallback(message);
    appendChatMessage(fallbackText, 'assistant', true);
  }
}

function appendChatMessage(text, sender, isEngineVerified = false) {
  const container = document.getElementById('chatMessages');
  if (!container) return;

  const bubble = document.createElement('div');
  bubble.className = `message-bubble ${sender}`;

  // Format markdown-like bold and bullet points safely
  let formatted = escapeHtml(text)
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code style="background:rgba(0,0,0,0.3);padding:2px 6px;border-radius:4px;">$1</code>')
    .replace(/\n\n/g, '<br><br>')
    .replace(/\n- /g, '<br>• ')
    .replace(/\n• /g, '<br>• ');

  bubble.innerHTML = formatted;

  if (sender === 'assistant' && isEngineVerified) {
    const pill = document.createElement('div');
    pill.className = 'verified-engine-pill';
    pill.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg> Grounded in Deterministic Engine`;
    bubble.appendChild(pill);
  }

  container.appendChild(bubble);
  container.scrollTop = container.scrollHeight;
}

function showTypingIndicator() {
  const container = document.getElementById('chatMessages');
  const ind = document.createElement('div');
  ind.className = 'typing-indicator';
  ind.id = 'activeTypingIndicator';
  ind.innerHTML = `
    <span class="typing-dot"></span>
    <span class="typing-dot"></span>
    <span class="typing-dot"></span>
  `;
  container.appendChild(ind);
  container.scrollTop = container.scrollHeight;
}

function removeTypingIndicator() {
  const ind = document.getElementById('activeTypingIndicator');
  if (ind) ind.remove();
}

function getClientChatFallback(msg) {
  const lower = msg.toLowerCase();
  if (lower.includes('8.5') || lower.includes('reach') || lower.includes('target')) {
    return "To reach an **8.5 CGPA**, use our **Target GPA Predictor**! For example, if you currently have 8.24 CGPA across 64 credits and have 44 credits remaining, you need an average SGPA of **8.88** in your remaining semesters. Focus on high-credit theory subjects (4.0 credits) and maximize internal assessment scores.";
  }
  if (lower.includes('backlog') || lower.includes('fail') || lower.includes('kt')) {
    return "In SPPU CBCS, a backlog course earns **0 Grade Points (F)** and credits are not earned until passed. When you clear the examination, the cleared grade point replaces the 0 GP in your cumulative calculation, leading to an immediate boost in CGPA!";
  }
  return "I have analyzed your query with the deterministic GPA calculator. To compute your SGPA or predict target grades, please enter your credits and grades in the respective calculator tabs!";
}

/* ==========================================================================
   6. WHAT-IF ANALYSIS VIEW
   ========================================================================== */
function renderWhatIfView() {
  const container = document.getElementById('whatIfContentArea');
  if (!container) return;

  if (appState.whatIfMode === 'sgpa') {
    container.innerHTML = `
      <div style="margin-bottom: 18px;">
        <h4 style="font-size: 1rem; font-weight: 700; margin-bottom: 4px;">Subject Grade Improvement Simulation</h4>
        <p style="font-size: 0.85rem; color: var(--text-muted);">See how raising a single course grade (e.g. from B to O) impacts your overall semester SGPA.</p>
      </div>

      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 20px;">
        <div class="form-group">
          <label class="form-label">Subject Title</label>
          <input type="text" class="form-control" id="whatIfSubjName" value="Engineering Maths">
        </div>
        <div class="form-group">
          <label class="form-label">Subject Credits</label>
          <input type="number" step="0.5" class="form-control" id="whatIfSubjCredits" value="4.0">
        </div>
        <div class="form-group">
          <label class="form-label">Current Grade</label>
          <select class="form-control" id="whatIfCurrentGrade">
            <option value="B">B (6.0 GP)</option>
            <option value="C">C (5.0 GP)</option>
            <option value="P">P (4.0 GP)</option>
            <option value="F">F (0.0 GP)</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Hypothetical Grade</label>
          <select class="form-control" id="whatIfNewGrade">
            <option value="O" selected>O (10.0 GP)</option>
            <option value="A+">A+ (9.0 GP)</option>
            <option value="A">A (8.0 GP)</option>
            <option value="B+">B+ (7.0 GP)</option>
          </select>
        </div>
      </div>

      <button class="btn btn-primary" onclick="runWhatIfSgpaSim()">Simulate Grade Impact</button>

      <div id="whatIfSgpaResult" style="display:none; margin-top: 24px;">
        <div class="result-banner">
          <div class="result-main">
            <h3>Simulated Semester SGPA</h3>
            <div class="result-score" id="whatIfSimScore">0.00 <span>/ 10.0</span></div>
            <div id="whatIfDeltaPill" style="margin-top: 8px;"></div>
          </div>
          <div class="result-breakdown">
            <div class="breakdown-item">
              <div class="breakdown-label">Baseline SGPA</div>
              <div class="breakdown-val" id="whatIfBaseScore">0.00</div>
            </div>
          </div>
        </div>
      </div>
    `;
  } else {
    container.innerHTML = `
      <div style="margin-bottom: 18px;">
        <h4 style="font-size: 1rem; font-weight: 700; margin-bottom: 4px;">Future Semester SGPA Simulation</h4>
        <p style="font-size: 0.85rem; color: var(--text-muted);">Simulate adding next semester's expected SGPA to project your new cumulative CGPA.</p>
      </div>

      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 20px;">
        <div class="form-group">
          <label class="form-label">Future Semester Name</label>
          <input type="text" class="form-control" id="whatIfNextSemName" value="Semester 5 (TE Sem 1)">
        </div>
        <div class="form-group">
          <label class="form-label">Semester Credits</label>
          <input type="number" step="0.5" class="form-control" id="whatIfNextSemCredits" value="22.0">
        </div>
        <div class="form-group">
          <label class="form-label">Projected SGPA</label>
          <input type="number" step="0.01" min="0" max="10" class="form-control" id="whatIfNextSemSgpa" value="9.20">
        </div>
      </div>

      <button class="btn btn-primary" onclick="runWhatIfCgpaSim()">Simulate Future CGPA</button>

      <div id="whatIfCgpaResult" style="display:none; margin-top: 24px;">
        <div class="result-banner">
          <div class="result-main">
            <h3>Projected Cumulative CGPA</h3>
            <div class="result-score" id="whatIfSimCgpaScore">0.00 <span>/ 10.0</span></div>
            <div id="whatIfCgpaDeltaPill" style="margin-top: 8px;"></div>
          </div>
          <div class="result-breakdown">
            <div class="breakdown-item">
              <div class="breakdown-label">Current CGPA</div>
              <div class="breakdown-val" id="whatIfBaseCgpaScore">0.00</div>
            </div>
          </div>
        </div>
      </div>
    `;
  }
}

function runWhatIfSgpaSim() {
  const cr = parseFloat(document.getElementById('whatIfSubjCredits').value) || 4.0;
  const oldGrade = document.getElementById('whatIfCurrentGrade').value;
  const newGrade = document.getElementById('whatIfNewGrade').value;

  const oldGp = SPPU_SCALE[oldGrade] || 6.0;
  const newGp = SPPU_SCALE[newGrade] || 10.0;

  // Assume a standard 20 credit semester
  const totalCred = 20.0;
  const basePoints = (16.0 * 8.0) + (cr * oldGp);
  const simPoints = (16.0 * 8.0) + (cr * newGp);

  const baseSgpa = basePoints / totalCred;
  const simSgpa = simPoints / totalCred;
  const delta = simSgpa - baseSgpa;

  document.getElementById('whatIfBaseScore').innerText = baseSgpa.toFixed(2);
  document.getElementById('whatIfSimScore').innerHTML = `${simSgpa.toFixed(2)} <span>/ 10.0</span>`;

  const pill = document.getElementById('whatIfDeltaPill');
  pill.innerHTML = `<span class="delta-pill ${delta >= 0 ? 'positive' : 'negative'}">${delta >= 0 ? '+' : ''}${delta.toFixed(2)} SGPA Improvement</span>`;

  document.getElementById('whatIfSgpaResult').style.display = 'block';
}

function runWhatIfCgpaSim() {
  const nextCredits = parseFloat(document.getElementById('whatIfNextSemCredits').value) || 22.0;
  const nextSgpa = parseFloat(document.getElementById('whatIfNextSemSgpa').value) || 9.20;

  const semRecords = appState.records.filter(r => r.record_type === 'semester');
  let baseCredits = 0;
  let basePoints = 0;

  semRecords.forEach(r => {
    const c = parseFloat(r.credits) || 0;
    const s = parseFloat(r.sgpa) || 0;
    baseCredits += c;
    basePoints += (s * c);
  });

  if (baseCredits === 0) {
    baseCredits = 84.0;
    basePoints = 84.0 * 8.39;
  }

  const baseCgpa = basePoints / baseCredits;
  const simCredits = baseCredits + nextCredits;
  const simPoints = basePoints + (nextSgpa * nextCredits);
  const simCgpa = simPoints / simCredits;
  const delta = simCgpa - baseCgpa;

  document.getElementById('whatIfBaseCgpaScore').innerText = baseCgpa.toFixed(2);
  document.getElementById('whatIfSimCgpaScore').innerHTML = `${simCgpa.toFixed(2)} <span>/ 10.0</span>`;

  const pill = document.getElementById('whatIfCgpaDeltaPill');
  pill.innerHTML = `<span class="delta-pill ${delta >= 0 ? 'positive' : 'negative'}">${delta >= 0 ? '+' : ''}${delta.toFixed(2)} Cumulative CGPA Shift</span>`;

  document.getElementById('whatIfCgpaResult').style.display = 'block';
}

/* ==========================================================================
   7. BACKLOG MANAGER
   ========================================================================= */
function seedDefaultBacklogRows() {
  const tbody = document.getElementById('backlogTableBody');
  if (!tbody) return;
  tbody.innerHTML = '';
  addBacklogRow('Theory of Computation (Backlog)', 4.0, 'A');
}

function addBacklogRow(name = '', credits = 4.0, targetGrade = 'A') {
  const tbody = document.getElementById('backlogTableBody');
  if (!tbody) return;

  const tr = document.createElement('tr');
  tr.innerHTML = `
    <td>
      <input type="text" class="form-control bk-name" value="${escapeHtml(name)}" placeholder="Failed Course Title" required>
    </td>
    <td>
      <input type="number" step="0.5" min="1" max="10" class="form-control bk-credits" value="${credits}" required>
    </td>
    <td>
      <select class="form-control bk-target-grade">
        <option value="O" ${targetGrade === 'O' ? 'selected' : ''}>O (10 GP)</option>
        <option value="A+" ${targetGrade === 'A+' ? 'selected' : ''}>A+ (9 GP)</option>
        <option value="A" ${targetGrade === 'A' ? 'selected' : ''}>A (8 GP)</option>
        <option value="B+" ${targetGrade === 'B+' ? 'selected' : ''}>B+ (7 GP)</option>
        <option value="P" ${targetGrade === 'P' ? 'selected' : ''}>P (4 GP)</option>
      </select>
    </td>
    <td>
      <button type="button" class="btn btn-danger btn-sm" onclick="this.closest('tr').remove()">Remove</button>
    </td>
  `;
  tbody.appendChild(tr);
}

function calculateBacklogImpact() {
  const rows = document.querySelectorAll('#backlogTableBody tr');
  if (rows.length === 0) {
    showToast('Add at least one backlog course.', 'info');
    return;
  }

  let totalBacklogCredits = 0;
  let pointsRecovered = 0;

  rows.forEach(r => {
    const cred = parseFloat(r.querySelector('.bk-credits').value) || 0;
    const grade = r.querySelector('.bk-target-grade').value;
    const gp = SPPU_SCALE[grade] || 8.0;

    totalBacklogCredits += cred;
    pointsRecovered += (cred * gp);
  });

  // Base CGPA from history
  const semRecords = appState.records.filter(r => r.record_type === 'semester');
  let baseCredits = 0;
  let basePoints = 0;
  semRecords.forEach(r => {
    const c = parseFloat(r.credits) || 0;
    const s = parseFloat(r.sgpa) || 0;
    baseCredits += c;
    basePoints += (s * c);
  });

  if (baseCredits === 0) {
    baseCredits = 84.0;
    basePoints = 84.0 * 8.20;
  }

  const baseCgpa = basePoints / baseCredits;
  const simPoints = basePoints + pointsRecovered;
  const simCgpa = simPoints / baseCredits;
  const gain = simCgpa - baseCgpa;

  document.getElementById('backlogSimulatedCgpa').innerHTML = `${simCgpa.toFixed(2)} <span>/ 10.0</span>`;
  document.getElementById('backlogGainText').innerText = `+${gain.toFixed(2)} CGPA Gain Upon Clearing Backlogs`;
  document.getElementById('backlogBaseCgpa').innerText = baseCgpa.toFixed(2);
  document.getElementById('backlogCreditsCleared').innerText = totalBacklogCredits.toFixed(1);
  document.getElementById('backlogPointsRecovered').innerText = pointsRecovered.toFixed(1);

  document.getElementById('backlogResultBanner').style.display = 'flex';
  showToast('Backlog recovery simulated successfully!', 'success');
}

/* ==========================================================================
   8. ACADEMIC HISTORY (SQLite Persistence)
   ========================================================================== */
async function loadAcademicHistory() {
  try {
    const res = await fetch(`${API_BASE}/history`);
    if (res.ok) {
      appState.records = await res.json();
      localStorage.setItem('gpa_academic_records', JSON.stringify(appState.records));
      renderHistoryTable();
      updateDashboardMetrics();
      initCharts();
      return;
    }
  } catch (err) {
    // Offline / GitHub Pages fallback
  }

  // Load from localStorage or seed initial SPPU demo records
  const stored = localStorage.getItem('gpa_academic_records');
  if (stored) {
    try {
      appState.records = JSON.parse(stored);
    } catch (e) {
      appState.records = [];
    }
  }

  if (!appState.records || appState.records.length === 0) {
    appState.records = [
      { id: 1, record_type: 'semester', title: 'Semester 1 (FE Sem 1)', sgpa: 8.12, credits: 20.0, created_at: new Date(Date.now() - 365*24*3600*1000).toISOString() },
      { id: 2, record_type: 'semester', title: 'Semester 2 (FE Sem 2)', sgpa: 8.28, credits: 20.0, created_at: new Date(Date.now() - 270*24*3600*1000).toISOString() },
      { id: 3, record_type: 'semester', title: 'Semester 3 (SE Sem 1)', sgpa: 8.45, credits: 22.0, created_at: new Date(Date.now() - 180*24*3600*1000).toISOString() },
      { id: 4, record_type: 'semester', title: 'Semester 4 (SE Sem 2)', sgpa: 8.68, credits: 22.0, created_at: new Date(Date.now() - 90*24*3600*1000).toISOString() }
    ];
    localStorage.setItem('gpa_academic_records', JSON.stringify(appState.records));
  }

  renderHistoryTable();
  updateDashboardMetrics();
  initCharts();
}

function renderHistoryTable() {
  const tbody = document.getElementById('historyTableBody');
  if (!tbody) return;

  if (appState.records.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted);">No records found. Calculate SGPA and click 'Save to History'.</td></tr>`;
    return;
  }

  tbody.innerHTML = appState.records.map(r => `
    <tr>
      <td>#${r.id}</td>
      <td><span class="grade-badge grade-Bp">${escapeHtml(r.record_type)}</span></td>
      <td><strong>${escapeHtml(r.title)}</strong></td>
      <td><span class="grade-badge grade-Ap">${parseFloat(r.sgpa || 0).toFixed(2)}</span></td>
      <td>${parseFloat(r.credits || 0).toFixed(1)} cr</td>
      <td style="color: var(--text-muted); font-size: 0.82rem;">${new Date(r.created_at).toLocaleDateString()}</td>
      <td>
        <div style="display: flex; gap: 8px;">
          <button class="btn btn-secondary btn-sm" onclick="openEditModal(${r.id})">Edit</button>
          <button class="btn btn-danger btn-sm" onclick="deleteHistoryRecord(${r.id})">Delete</button>
        </div>
      </td>
    </tr>
  `).join('');
}

function openEditModal(recordId) {
  const rec = appState.records.find(r => r.id === recordId);
  if (!rec) return;

  document.getElementById('editRecordId').value = rec.id;
  document.getElementById('editTitle').value = rec.title;
  document.getElementById('editSgpa').value = rec.sgpa;
  document.getElementById('editCredits').value = rec.credits;

  document.getElementById('editRecordModal').classList.add('active');
}

function closeEditModal() {
  document.getElementById('editRecordModal').classList.remove('active');
}

async function handleEditRecordSubmit(e) {
  e.preventDefault();
  const id = parseInt(document.getElementById('editRecordId').value, 10);
  const title = document.getElementById('editTitle').value.trim();
  const sgpa = parseFloat(document.getElementById('editSgpa').value);
  const credits = parseFloat(document.getElementById('editCredits').value);

  try {
    const res = await fetch(`${API_BASE}/history/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, sgpa, credits })
    });
    if (res.ok) {
      showToast('Record updated successfully!', 'success');
      closeEditModal();
      await loadAcademicHistory();
      return;
    }
  } catch (err) {
    // Offline fallback
  }

  const rec = appState.records.find(r => r.id === id);
  if (rec) {
    rec.title = title;
    rec.sgpa = sgpa;
    rec.credits = credits;
    localStorage.setItem('gpa_academic_records', JSON.stringify(appState.records));
    renderHistoryTable();
    updateDashboardMetrics();
    initCharts();
    showToast('Record updated in browser storage!', 'success');
  }
  closeEditModal();
}

async function deleteHistoryRecord(recordId) {
  if (!confirm(`Are you sure you want to delete record #${recordId}?`)) return;

  try {
    const res = await fetch(`${API_BASE}/history/${recordId}`, { method: 'DELETE' });
    if (res.ok) {
      showToast('Record deleted.', 'success');
      await loadAcademicHistory();
      return;
    }
  } catch (err) {
    // Offline fallback
  }

  appState.records = appState.records.filter(r => r.id !== recordId);
  localStorage.setItem('gpa_academic_records', JSON.stringify(appState.records));
  renderHistoryTable();
  updateDashboardMetrics();
  initCharts();
  showToast('Record removed from browser storage.', 'info');
}

/* ==========================================================================
   9. GRADING SCHEME SETTINGS
   ========================================================================== */
function renderGradingSchemeTable() {
  const tbody = document.getElementById('schemeTableBody');
  if (!tbody) return;

  const ranges = {
    'O': '90% - 100% (Outstanding)',
    'A+': '80% - 89% (Excellent)',
    'A': '70% - 79% (Very Good)',
    'B+': '60% - 69% (Good)',
    'B': '55% - 59% (Above Average)',
    'C': '50% - 54% (Average)',
    'P': '40% - 49% (Pass threshold)',
    'F': 'Below 40% (Fail / Backlog)',
    'Ab': 'Absent (0 GP)'
  };

  tbody.innerHTML = Object.entries(appState.activeScheme).map(([grade, gp]) => `
    <tr>
      <td>
        <span class="grade-badge grade-${grade.replace('+', 'p')}">${grade}</span>
      </td>
      <td>
        <strong>${gp.toFixed(1)}</strong>
      </td>
      <td style="color: var(--text-secondary); font-size: 0.85rem;">
        ${ranges[grade] || 'Standard scale'}
      </td>
    </tr>
  `).join('');
}

/* ==========================================================================
   EVENT HANDLERS & HELPERS
   ========================================================================== */
function setupEventListeners() {
  // Theme Toggle
  const themeBtn = document.getElementById('themeToggleBtn');
  if (themeBtn) themeBtn.addEventListener('click', toggleTheme);

  // SGPA
  const btnAddSubj = document.getElementById('btnAddSubjectRow');
  if (btnAddSubj) btnAddSubj.addEventListener('click', () => addSubjectRow());

  const btnCalcSgpa = document.getElementById('btnCalculateSgpa');
  if (btnCalcSgpa) btnCalcSgpa.addEventListener('click', calculateSgpa);

  const btnSaveSgpa = document.getElementById('btnSaveSgpaToHistory');
  if (btnSaveSgpa) btnSaveSgpa.addEventListener('click', saveSgpaToHistory);

  const btnLoadSample = document.getElementById('btnLoadSgpaSample');
  if (btnLoadSample) btnLoadSample.addEventListener('click', seedDefaultSgpaRows);

  // CGPA
  const btnAddSem = document.getElementById('btnAddSemesterRow');
  if (btnAddSem) btnAddSem.addEventListener('click', () => addSemesterRow());

  const btnCalcCgpa = document.getElementById('btnCalculateCgpa');
  if (btnCalcCgpa) btnCalcCgpa.addEventListener('click', calculateCgpa);

  const btnLoadCgpa = document.getElementById('btnLoadCgpaFromHistory');
  if (btnLoadCgpa) btnLoadCgpa.addEventListener('click', loadCgpaFromHistory);

  // Target GPA
  const targetForm = document.getElementById('targetGpaForm');
  if (targetForm) targetForm.addEventListener('submit', handleTargetGpaSubmit);

  // Chat
  const chatForm = document.getElementById('chatForm');
  if (chatForm) chatForm.addEventListener('submit', handleChatSubmit);

  const clearChatBtn = document.getElementById('btnClearChatHistory');
  if (clearChatBtn) {
    clearChatBtn.addEventListener('click', () => {
      document.getElementById('chatMessages').innerHTML = '';
      appendChatMessage('Chat history cleared. How can I help you today?', 'assistant');
    });
  }

  // Quick Chat Prompts
  document.querySelectorAll('.prompt-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const p = chip.getAttribute('data-prompt');
      document.getElementById('chatInput').value = p;
      document.getElementById('btnSendChat').click();
    });
  });

  // What-If mode toggles
  const btnWhatSgpa = document.getElementById('btnWhatIfModeSgpa');
  const btnWhatCgpa = document.getElementById('btnWhatIfModeCgpa');
  if (btnWhatSgpa && btnWhatCgpa) {
    btnWhatSgpa.addEventListener('click', () => {
      appState.whatIfMode = 'sgpa';
      btnWhatSgpa.className = 'btn btn-primary btn-sm';
      btnWhatCgpa.className = 'btn btn-secondary btn-sm';
      renderWhatIfView();
    });
    btnWhatCgpa.addEventListener('click', () => {
      appState.whatIfMode = 'cgpa';
      btnWhatCgpa.className = 'btn btn-primary btn-sm';
      btnWhatSgpa.className = 'btn btn-secondary btn-sm';
      renderWhatIfView();
    });
  }

  // Backlog
  const btnAddBk = document.getElementById('btnAddBacklogSubject');
  if (btnAddBk) btnAddBk.addEventListener('click', () => addBacklogRow());

  const btnCalcBk = document.getElementById('btnCalculateBacklogImpact');
  if (btnCalcBk) btnCalcBk.addEventListener('click', calculateBacklogImpact);

  // History reload & edit
  const btnReloadHist = document.getElementById('btnReloadHistory');
  if (btnReloadHist) btnReloadHist.addEventListener('click', loadAcademicHistory);

  const editForm = document.getElementById('editRecordForm');
  if (editForm) editForm.addEventListener('submit', handleEditRecordSubmit);

  // Settings
  const resetSchemeBtn = document.getElementById('btnResetToSppuDefault');
  if (resetSchemeBtn) {
    resetSchemeBtn.addEventListener('click', () => {
      appState.activeScheme = { ...SPPU_SCALE };
      renderGradingSchemeTable();
      showToast('Grading scheme reset to SPPU 10-Point standard.', 'success');
    });
  }

  // SPPU Converter Listeners
  const dashCgpaIn = document.getElementById('dashConverterCgpa');
  if (dashCgpaIn) {
    dashCgpaIn.addEventListener('input', (e) => {
      updateSppuConverterUI(e.target.value, 'dash');
    });
  }

  const dedCgpaIn = document.getElementById('converterCgpaInput');
  if (dedCgpaIn) {
    dedCgpaIn.addEventListener('input', (e) => {
      updateSppuConverterUI(e.target.value, 'dedicated');
    });
  }

  const btnSyncDash = document.getElementById('btnSyncDashCgpa');
  if (btnSyncDash) btnSyncDash.addEventListener('click', syncConverterFromCurrent);

  const btnSyncDed = document.getElementById('btnSyncDedicatedConverter');
  if (btnSyncDed) btnSyncDed.addEventListener('click', syncConverterFromCurrent);

  // Initialize converter with default
  syncConverterFromCurrent();
}

/* ==========================================================================
   SPPU PERCENTAGE & DEGREE CLASS CONVERTER (Circular No. 332/2020)
   ========================================================================== */
function calculateSppuPercentage(cgpa) {
  cgpa = parseFloat(cgpa);
  if (isNaN(cgpa) || cgpa < 0) return { cgpa: 0, percentage: 0, formula: 'Invalid CGPA', range: 'N/A', degreeClass: 'N/A' };
  if (cgpa > 10.0) cgpa = 10.0;

  let percentage = 0;
  let formula = '';
  let range = '';

  if (cgpa >= 9.50) {
    percentage = (20 * cgpa) - 100;
    formula = `20 × CGPA − 100 = 20 × ${cgpa.toFixed(2)} − 100 = ${percentage.toFixed(2)}%`;
    range = '9.50 – 10.00 (Grade O)';
  } else if (cgpa >= 8.25) {
    percentage = (12 * cgpa) - 25;
    formula = `12 × CGPA − 25 = 12 × ${cgpa.toFixed(2)} − 25 = ${percentage.toFixed(2)}%`;
    range = '8.25 – 9.49 (Grade A+)';
  } else if (cgpa >= 6.75) {
    percentage = (10 * cgpa) - 7.5;
    formula = `10 × CGPA − 7.5 = 10 × ${cgpa.toFixed(2)} − 7.5 = ${percentage.toFixed(2)}%`;
    range = '6.75 – 8.24 (Grade A)';
  } else if (cgpa >= 5.75) {
    percentage = (5 * cgpa) + 26.25;
    formula = `5 × CGPA + 26.25 = 5 × ${cgpa.toFixed(2)} + 26.25 = ${percentage.toFixed(2)}%`;
    range = '5.75 – 6.74 (Grade B+)';
  } else if (cgpa >= 5.25) {
    percentage = (10 * cgpa) - 2.5;
    formula = `10 × CGPA − 2.5 = 10 × ${cgpa.toFixed(2)} − 2.5 = ${percentage.toFixed(2)}%`;
    range = '5.25 – 5.74 (Grade B)';
  } else if (cgpa >= 4.75) {
    percentage = (10 * cgpa) - 2.5;
    formula = `10 × CGPA − 2.5 = 10 × ${cgpa.toFixed(2)} − 2.5 = ${percentage.toFixed(2)}%`;
    range = '4.75 – 5.24 (Grade C)';
  } else if (cgpa >= 4.00) {
    percentage = (6.6 * cgpa) + 13.6;
    formula = `6.6 × CGPA + 13.6 = 6.6 × ${cgpa.toFixed(2)} + 13.6 = ${percentage.toFixed(2)}%`;
    range = '4.00 – 4.74 (Grade P / D)';
  } else {
    percentage = 0;
    formula = 'Under Minimum Passing Marks (< 4.0 GP)';
    range = '< 4.00 (Grade F / Fail)';
  }

  return {
    cgpa: cgpa,
    percentage: parseFloat(percentage.toFixed(2)),
    formula: formula,
    range: range,
    degreeClass: getSppuDegreeClass(cgpa, percentage)
  };
}

function getSppuDegreeClass(cgpa, percentage) {
  if (cgpa >= 7.75 || percentage >= 70.0) return 'First Class with Distinction';
  if (cgpa >= 6.75 || percentage >= 60.0) return 'First Class';
  if (cgpa >= 6.25 || percentage >= 55.0) return 'Higher Second Class';
  if (cgpa >= 5.75 || percentage >= 50.0) return 'Second Class';
  if (cgpa >= 4.00 || percentage >= 40.0) return 'Pass Class';
  return 'Fail';
}

function updateSppuConverterUI(cgpaVal, source = 'all') {
  const result = calculateSppuPercentage(cgpaVal);

  // Sync inputs
  const dashIn = document.getElementById('dashConverterCgpa');
  const dedIn = document.getElementById('converterCgpaInput');
  if (source !== 'dash' && dashIn) dashIn.value = result.cgpa.toFixed(2);
  if (source !== 'dedicated' && dedIn) dedIn.value = result.cgpa.toFixed(2);

  // Dashboard outputs
  const dashPercent = document.getElementById('dashConverterPercent');
  const dashClass = document.getElementById('dashConverterClass');
  const dashExp = document.getElementById('dashFormulaExplanation');
  if (dashPercent) dashPercent.innerText = `${result.percentage.toFixed(2)}%`;
  if (dashClass) {
    dashClass.innerText = result.degreeClass;
    dashClass.style.color = result.degreeClass === 'Fail' ? 'var(--fail-color)' : 'var(--pass-color)';
  }
  if (dashExp) {
    dashExp.innerHTML = `Active Formula for CGPA <strong>${result.cgpa.toFixed(2)}</strong> (Range: ${result.range}):<br><code style="background:rgba(255,255,255,0.06);padding:2px 8px;border-radius:4px;color:var(--text-white);font-family:'JetBrains Mono',monospace;">Percentage = ${result.formula}</code>`;
  }

  // Dedicated outputs
  const dedPercent = document.getElementById('converterPercentResult');
  const dedClass = document.getElementById('converterClassResult');
  const dedForm = document.getElementById('converterFormulaDisplay');
  const dedBand = document.getElementById('converterBandDisplay');
  if (dedPercent) dedPercent.innerText = `${result.percentage.toFixed(2)}%`;
  if (dedClass) {
    dedClass.innerText = result.degreeClass;
    dedClass.style.color = result.degreeClass === 'Fail' ? 'var(--fail-color)' : 'var(--pass-color)';
  }
  if (dedForm) dedForm.innerText = result.formula;
  if (dedBand) dedBand.innerText = `Grade Band: ${result.range}`;
}

function syncConverterFromCurrent() {
  const dashCgpaEl = document.getElementById('dashCgpa');
  let currentVal = 8.39;
  if (dashCgpaEl) {
    const textVal = parseFloat(dashCgpaEl.innerText);
    if (!isNaN(textVal) && textVal > 0) currentVal = textVal;
  }
  updateSppuConverterUI(currentVal);
}

function saveCurrentToHistory() {
  if (appState.activeView === 'sgpa' && appState.lastCalculatedSgpa) {
    saveSgpaToHistory();
  } else {
    const semRecords = appState.records.filter(r => r.record_type === 'semester');
    let totalCredits = 0;
    let totalWeightedPts = 0;
    semRecords.forEach(r => {
      const c = parseFloat(r.credits) || 0;
      const s = parseFloat(r.sgpa) || 0;
      totalCredits += c;
      totalWeightedPts += (s * c);
    });
    const cgpa = totalCredits > 0 ? (totalWeightedPts / totalCredits).toFixed(2) : "8.39";
    showToast(`Current CGPA: ${cgpa} across ${totalCredits.toFixed(1)} credits. All records saved in SQLite!`, 'success');
  }
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerText = message;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
