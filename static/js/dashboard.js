// Dashboard page JavaScript

let syncHistoryChart = null;
let automationStatusChart = null;
let _allSuitesStats = null;   // overall /testrail/stats response
let _bySuiteStats = null;     // /testrail/stats/by-suite response
let _activeSuiteId = 'all';

const STATUS_LABELS = {
    '0': 'Deleted',
    '1': 'Manual',
    '2': 'Obsolete',
    '3': 'Will Not Automate',
    '4': 'Automated',
    '5': 'To Be Automated',
    'null': 'No Status'
};

const STATUS_COLORS = {
    '0': 'rgba(220, 53, 69, 0.8)',
    '1': 'rgba(255, 193, 7, 0.8)',
    '2': 'rgba(52, 58, 64, 0.8)',
    '3': 'rgba(220, 53, 69, 0.8)',
    '4': 'rgba(25, 135, 84, 0.8)',
    '5': 'rgba(108, 117, 125, 0.8)',
    'null': 'rgba(173, 181, 189, 0.6)'
};

document.addEventListener('DOMContentLoaded', () => {
    loadDashboardData();
    loadLastSyncStatus();
    loadRecentTests();
    loadSyncHistory();
    loadAutomationStatusChart();
});

async function loadDashboardData() {
    try {
        const stats = await apiCall('/tests/stats');

        document.getElementById('total-tests').textContent = stats.total_tests;
        document.getElementById('tests-with-testrail').textContent = stats.tests_with_testrail;
        document.getElementById('tests-without-testrail').textContent = stats.tests_without_testrail;
        document.getElementById('archived-tests').textContent = stats.archived_tests;
        document.getElementById('tests-deleted-testrail').textContent = stats.tests_with_deleted_testrail || 0;
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

async function loadLastSyncStatus() {
    try {
        const syncStatus = await apiCall('/sync/status');

        const statusHtml = `
            <dl class="row mb-0">
                <dt class="col-sm-4">Status:</dt>
                <dd class="col-sm-8">${getStatusBadge(syncStatus.status)}</dd>

                <dt class="col-sm-4">Type:</dt>
                <dd class="col-sm-8">${syncStatus.sync_type}</dd>

                <dt class="col-sm-4">Started:</dt>
                <dd class="col-sm-8">${formatDate(syncStatus.started_at)}</dd>

                <dt class="col-sm-4">Completed:</dt>
                <dd class="col-sm-8">${formatDate(syncStatus.completed_at)}</dd>

                <dt class="col-sm-4">Duration:</dt>
                <dd class="col-sm-8">${formatDuration(syncStatus.started_at, syncStatus.completed_at)}</dd>

                <dt class="col-sm-4">Tests Found:</dt>
                <dd class="col-sm-8">${syncStatus.tests_found || 0}</dd>

                <dt class="col-sm-4">Tests Synced:</dt>
                <dd class="col-sm-8">${syncStatus.tests_synced || 0}</dd>

                <dt class="col-sm-4">Branch:</dt>
                <dd class="col-sm-8">${syncStatus.branch || 'N/A'}</dd>

                <dt class="col-sm-4">Commit:</dt>
                <dd class="col-sm-8"><code>${syncStatus.commit_hash ? syncStatus.commit_hash.substring(0, 8) : 'N/A'}</code></dd>
            </dl>
        `;

        document.getElementById('last-sync-status').innerHTML = statusHtml;
    } catch (error) {
        document.getElementById('last-sync-status').innerHTML = '<p class="text-muted mb-0">No sync operations found.</p>';
    }
}

async function loadRecentTests() {
    try {
        const data = await apiCall('/tests?per_page=5');
        const tbody = document.querySelector('#recent-tests-table tbody');

        if (data.tests.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No tests found</td></tr>';
            return;
        }

        tbody.innerHTML = data.tests.map(test => `
            <tr>
                <td><a href="/tests/${test.id}">${test.test_name}</a></td>
                <td><small class="text-muted">${test.test_file}</small></td>
                <td>${formatTestRailIds(test.testrail_case_id)}</td>
                <td>${getStatusBadge(test.status)}</td>
                <td>
                    <a href="/tests/${test.id}" class="btn btn-sm btn-outline-primary">
                        <i class="bi bi-eye"></i>
                    </a>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading recent tests:', error);
    }
}

async function loadSyncHistory() {
    try {
        const data = await apiCall('/sync/logs?per_page=10');

        if (data.logs.length === 0) {
            return;
        }

        const ctx = document.getElementById('syncHistoryChart').getContext('2d');

        const labels = data.logs.reverse().map(log => {
            const date = new Date(log.started_at);
            return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
        });

        const testsFound = data.logs.map(log => log.tests_found || 0);
        const testsSynced = data.logs.map(log => log.tests_synced || 0);

        if (syncHistoryChart) {
            syncHistoryChart.destroy();
        }

        syncHistoryChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Tests Found',
                        data: testsFound,
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        tension: 0.1
                    },
                    {
                        label: 'Tests Synced',
                        data: testsSynced,
                        borderColor: 'rgb(54, 162, 235)',
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error loading sync history:', error);
    }
}

// ---------------------------------------------------------------------------
// Automation Status Chart – suite-aware
// ---------------------------------------------------------------------------

async function loadAutomationStatusChart() {
    try {
        // Fetch overall stats and per-suite stats in parallel
        const [overallData, suiteData] = await Promise.all([
            apiCall('/testrail/stats'),
            apiCall('/testrail/stats/by-suite')
        ]);

        _allSuitesStats = overallData;
        _bySuiteStats   = suiteData;

        _buildSuiteTabs(suiteData.suites || []);
        _renderAutomationChart('all');

        _buildExplicitSuiteTabs(suiteData.suites || []);
        _renderExplicitCoverageWidget('all');

    } catch (error) {
        console.error('Error loading automation status chart:', error);
        document.getElementById('automation-status-legend').innerHTML =
            '<p class="text-muted">Error loading automation status data</p>';
        document.getElementById('suite-filter-tabs').innerHTML = '';
        document.getElementById('explicit-coverage-widget').innerHTML =
            '<p class="text-muted">Error loading explicit coverage data</p>';
    }
}

function _buildSuiteTabs(suites) {
    const container = document.getElementById('suite-filter-tabs');
    if (!container) return;

    const tabs = [
        { id: 'all', label: '<i class="bi bi-grid"></i> All Suites' },
        ...suites.map(s => ({
            id: s.suite_id,
            label: `<i class="bi bi-folder2"></i> ${s.suite_name || 'Suite ' + s.suite_id}`
        }))
    ];

    container.innerHTML = tabs.map((tab, i) => `
        <button class="btn btn-sm ${i === 0 ? 'btn-primary' : 'btn-outline-secondary'} suite-tab-btn"
                data-suite-id="${tab.id}">
            ${tab.label}
        </button>
    `).join('');

    container.querySelectorAll('.suite-tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            container.querySelectorAll('.suite-tab-btn').forEach(b => {
                b.classList.remove('btn-primary');
                b.classList.add('btn-outline-secondary');
            });
            btn.classList.remove('btn-outline-secondary');
            btn.classList.add('btn-primary');

            _activeSuiteId = btn.dataset.suiteId;
            _renderAutomationChart(_activeSuiteId);
        });
    });
}

function _renderAutomationChart(suiteId) {
    let breakdown, totalCases, automatedCount, automationPct, suiteLabel;

    if (suiteId === 'all') {
        breakdown       = _allSuitesStats.automation_status_breakdown;
        totalCases      = _allSuitesStats.total_cases;
        automatedCount  = _allSuitesStats.automated_count;
        automationPct   = _allSuitesStats.automation_percentage;
        suiteLabel      = 'All Suites';
    } else {
        const suite = (_bySuiteStats.suites || []).find(s => s.suite_id === suiteId);
        if (!suite) return;
        breakdown       = suite.automation_status_breakdown;
        totalCases      = suite.total_cases;
        automatedCount  = suite.automated_count;
        automationPct   = suite.automation_percentage;
        suiteLabel      = suite.suite_name || `Suite ${suite.suite_id}`;
    }

    // Build chart arrays (skip zero-count entries)
    const labels = [], counts = [], colors = [];
    Object.keys(breakdown).forEach(key => {
        if (breakdown[key] > 0) {
            labels.push(STATUS_LABELS[key] || key);
            counts.push(breakdown[key]);
            colors.push(STATUS_COLORS[key] || 'rgba(108,117,125,0.8)');
        }
    });

    // Draw / redraw doughnut chart
    const ctx = document.getElementById('automationStatusChart').getContext('2d');
    if (automationStatusChart) automationStatusChart.destroy();

    automationStatusChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data: counts,
                backgroundColor: colors,
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: { padding: 15, font: { size: 12 } }
                },
                tooltip: {
                    callbacks: {
                        label(context) {
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const pct = ((value / total) * 100).toFixed(1);
                            return `${context.label}: ${value} (${pct}%)`;
                        }
                    }
                }
            }
        }
    });

    // Legend panel
    document.getElementById('automation-status-legend').innerHTML = `
        <h6 class="mb-1 fw-semibold">${suiteLabel}</h6>
        <div class="mb-3">
            <div class="d-flex justify-content-between small text-muted mb-1">
                <span>Automation coverage</span>
                <strong class="text-success">${automationPct}%</strong>
            </div>
            <div class="progress" style="height:8px;">
                <div class="progress-bar bg-success" style="width:${automationPct}%"
                     title="${automatedCount} automated"></div>
            </div>
        </div>
        <div class="list-group list-group-flush">
            ${labels.map((lbl, i) => `
                <div class="list-group-item d-flex justify-content-between align-items-center px-0 py-1">
                    <div>
                        <span style="display:inline-block;width:12px;height:12px;
                                     background:${colors[i]};border-radius:2px;margin-right:8px;"></span>
                        <small>${lbl}</small>
                    </div>
                    <span class="badge bg-secondary rounded-pill">${counts[i]}</span>
                </div>
            `).join('')}
        </div>
        <div class="mt-3 pt-3 border-top">
            <strong>Total Cases: ${totalCases}</strong>
        </div>
    `;

    // Suite comparison bars (only in All-Suites view with multiple suites)
    _renderSuiteComparisonBars(suiteId);
}

function _renderSuiteComparisonBars(activeSuiteId) {
    const container = document.getElementById('suite-comparison-bars');
    if (!container) return;

    const suites = (_bySuiteStats && _bySuiteStats.suites) || [];

    if (activeSuiteId !== 'all' || suites.length <= 1) {
        container.innerHTML = '';
        return;
    }

    const barsHtml = suites.map(suite => {
        const bd  = suite.automation_status_breakdown;
        const tot = suite.total_cases || 1;

        const automatedPct  = ((bd['4']    || 0) / tot * 100).toFixed(1);
        const manualPct     = ((bd['1']    || 0) / tot * 100).toFixed(1);
        const toAutomatePct = ((bd['5']    || 0) / tot * 100).toFixed(1);
        const wontAutoPct   = ((bd['3']    || 0) / tot * 100).toFixed(1);
        const otherPct      = (100 - parseFloat(automatedPct) - parseFloat(manualPct)
                                   - parseFloat(toAutomatePct) - parseFloat(wontAutoPct)).toFixed(1);

        return `
            <div class="mb-3">
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <span class="fw-semibold">${suite.suite_name || 'Suite ' + suite.suite_id}</span>
                    <span class="badge bg-success">${suite.automation_percentage}% automated</span>
                </div>
                <div class="progress" style="height:20px;border-radius:6px;" title="${suite.suite_name}">
                    <div class="progress-bar bg-success"
                         style="width:${automatedPct}%"
                         title="Automated: ${bd['4'] || 0}">
                        ${parseFloat(automatedPct) > 6 ? automatedPct + '%' : ''}
                    </div>
                    <div class="progress-bar bg-warning text-dark"
                         style="width:${manualPct}%"
                         title="Manual: ${bd['1'] || 0}">
                        ${parseFloat(manualPct) > 6 ? manualPct + '%' : ''}
                    </div>
                    <div class="progress-bar"
                         style="width:${toAutomatePct}%;background:rgba(108,117,125,0.7);"
                         title="To Be Automated: ${bd['5'] || 0}">
                        ${parseFloat(toAutomatePct) > 6 ? toAutomatePct + '%' : ''}
                    </div>
                    <div class="progress-bar bg-danger"
                         style="width:${wontAutoPct}%"
                         title="Will Not Automate: ${bd['3'] || 0}">
                        ${parseFloat(wontAutoPct) > 6 ? wontAutoPct + '%' : ''}
                    </div>
                    <div class="progress-bar bg-light text-dark"
                         style="width:${Math.max(0, parseFloat(otherPct))}%"
                         title="Other / No Status">
                    </div>
                </div>
                <div class="d-flex gap-3 mt-1" style="font-size:11px;color:#6c757d;">
                    <span><strong>${suite.total_cases}</strong> total</span>
                    <span style="color:#198754;"><strong>${bd['4'] || 0}</strong> automated</span>
                    <span style="color:#ffc107;"><strong>${bd['1'] || 0}</strong> manual</span>
                    <span><strong>${bd['5'] || 0}</strong> to automate</span>
                    <span style="color:#dc3545;"><strong>${bd['3'] || 0}</strong> won't automate</span>
                </div>
            </div>
        `;
    }).join('<hr class="my-2">');

    // Legend for the stacked bars
    const legendItems = [
        { color: '#198754', label: 'Automated' },
        { color: '#ffc107', label: 'Manual' },
        { color: 'rgba(108,117,125,0.7)', label: 'To Be Automated' },
        { color: '#dc3545', label: 'Will Not Automate' },
        { color: '#e9ecef', label: 'Other / No Status' }
    ];

    const legendHtml = legendItems.map(item => `
        <span class="d-flex align-items-center gap-1 me-3 small">
            <span style="display:inline-block;width:12px;height:12px;
                         background:${item.color};border-radius:2px;"></span>
            ${item.label}
        </span>
    `).join('');

    container.innerHTML = `
        <hr class="mt-2 mb-3">
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h6 class="mb-0 text-muted">
                <i class="bi bi-bar-chart-steps"></i> Suite-wise Comparison
            </h6>
            <div class="d-flex flex-wrap">${legendHtml}</div>
        </div>
        ${barsHtml}
    `;
}

// ---------------------------------------------------------------------------
// Explicit Automation Coverage Widget
// ---------------------------------------------------------------------------

function _buildExplicitSuiteTabs(suites) {
    const container = document.getElementById('explicit-suite-filter-tabs');
    if (!container) return;

    const tabs = [
        { id: 'all', label: '<i class="bi bi-grid"></i> All Suites' },
        ...suites.map(s => ({
            id: s.suite_id,
            label: `<i class="bi bi-folder2"></i> ${s.suite_name || 'Suite ' + s.suite_id}`
        }))
    ];

    container.innerHTML = tabs.map((tab, i) => `
        <button class="btn btn-sm ${i === 0 ? 'btn-primary' : 'btn-outline-secondary'} explicit-suite-tab-btn"
                data-suite-id="${tab.id}">
            ${tab.label}
        </button>
    `).join('');

    container.querySelectorAll('.explicit-suite-tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            container.querySelectorAll('.explicit-suite-tab-btn').forEach(b => {
                b.classList.remove('btn-primary');
                b.classList.add('btn-outline-secondary');
            });
            btn.classList.remove('btn-outline-secondary');
            btn.classList.add('btn-primary');
            _renderExplicitCoverageWidget(btn.dataset.suiteId);
        });
    });
}

function _renderExplicitCoverageWidget(suiteId) {
    const container = document.getElementById('explicit-coverage-widget');
    if (!container) return;

    // Helper to render one suite's explicit coverage block
    function _suiteBlock(suiteName, automatedCount, manualCount, explicitTotal, explicitPct, totalCases, highlight) {
        const barColor   = explicitPct >= 75 ? '#198754' : explicitPct >= 50 ? '#0d6efd' : '#ffc107';
        const badgeCls   = explicitPct >= 75 ? 'bg-success' : explicitPct >= 50 ? 'bg-primary' : 'bg-warning text-dark';
        const borderCls  = highlight ? 'border-2 border-primary shadow-sm' : '';

        return `
            <div class="col">
                <div class="card h-100 ${borderCls}">
                    <div class="card-body py-3">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h6 class="fw-semibold mb-0">${suiteName}</h6>
                            <span class="badge ${badgeCls} fs-6 ms-2">${explicitPct}%</span>
                        </div>

                        <!-- Big gauge progress bar -->
                        <div class="progress mb-2" style="height:18px;border-radius:6px;"
                             title="${automatedCount} Automated out of ${explicitTotal} (Automated + Manual)">
                            <div class="progress-bar"
                                 style="width:${explicitPct}%;background:${barColor};font-size:12px;font-weight:600;">
                                ${explicitPct > 12 ? explicitPct + '%' : ''}
                            </div>
                        </div>

                        <!-- Counts row -->
                        <div class="row g-2 text-center mt-1">
                            <div class="col-4">
                                <div class="border rounded py-2 px-1">
                                    <div class="fw-bold text-success" style="font-size:1.1rem;">${automatedCount}</div>
                                    <div class="text-muted" style="font-size:10px;">Automated</div>
                                </div>
                            </div>
                            <div class="col-4">
                                <div class="border rounded py-2 px-1">
                                    <div class="fw-bold text-warning" style="font-size:1.1rem;">${manualCount}</div>
                                    <div class="text-muted" style="font-size:10px;">Manual</div>
                                </div>
                            </div>
                            <div class="col-4">
                                <div class="border rounded py-2 px-1">
                                    <div class="fw-bold" style="font-size:1.1rem;">${explicitTotal}</div>
                                    <div class="text-muted" style="font-size:10px;">Explicit Total</div>
                                </div>
                            </div>
                        </div>

                        <div class="text-muted mt-2" style="font-size:11px;">
                            <i class="bi bi-info-circle"></i>
                            ${totalCases} total cases in TestRail
                            &nbsp;|&nbsp; ${totalCases - explicitTotal} excluded from denominator
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    if (suiteId === 'all') {
        // Overall card + one card per suite
        const overallBlock = _suiteBlock(
            'All Suites',
            _allSuitesStats.automated_count,
            _allSuitesStats.manual_count,
            _allSuitesStats.explicit_total,
            _allSuitesStats.explicit_automation_percentage,
            _allSuitesStats.total_cases,
            false
        );

        const suiteBlocks = (_bySuiteStats.suites || []).map(s =>
            _suiteBlock(
                s.suite_name || `Suite ${s.suite_id}`,
                s.automated_count,
                s.manual_count,
                s.explicit_total,
                s.explicit_automation_percentage,
                s.total_cases,
                false
            )
        ).join('');

        container.innerHTML = `<div class="row g-3 row-cols-1 row-cols-md-3">${overallBlock}${suiteBlocks}</div>`;

    } else {
        // Single suite view
        const suite = (_bySuiteStats.suites || []).find(s => s.suite_id === suiteId);
        if (!suite) return;

        container.innerHTML = `
            <div class="row g-3 row-cols-1 row-cols-md-2">
                ${_suiteBlock(
                    suite.suite_name || `Suite ${suite.suite_id}`,
                    suite.automated_count,
                    suite.manual_count,
                    suite.explicit_total,
                    suite.explicit_automation_percentage,
                    suite.total_cases,
                    true
                )}
                <div class="col d-flex align-items-center">
                    <div class="p-3 bg-light rounded w-100">
                        <h6 class="fw-semibold text-muted mb-3">
                            <i class="bi bi-calculator"></i> How it's calculated
                        </h6>
                        <div class="mb-2">
                            <code class="d-block p-2 bg-white border rounded" style="font-size:13px;">
                                Explicit Coverage = Automated ÷ (Automated + Manual) × 100
                            </code>
                        </div>
                        <ul class="small text-muted mb-0 mt-2 ps-3">
                            <li><strong>Automated (${suite.automated_count})</strong> — status 4</li>
                            <li><strong>Manual (${suite.manual_count})</strong> — status 1</li>
                            <li>Excluded from denominator: Obsolete, Will Not Automate,
                                To Be Automated, No Status
                                (${suite.total_cases - suite.explicit_total} cases)</li>
                        </ul>
                    </div>
                </div>
            </div>
        `;
    }
}

