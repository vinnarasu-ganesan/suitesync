// Dashboard page JavaScript

let syncHistoryChart = null;
let automationStatusChart = null;

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

async function loadAutomationStatusChart() {
    try {
        const data = await apiCall('/testrail/stats');

        if (!data.automation_status_breakdown) {
            console.error('No automation status breakdown data');
            return;
        }

        const statusLabels = {
            '0': 'Deleted',
            '1': 'Manual',
            '2': 'Obsolete',
            '3': 'Will Not Automate',
            '4': 'Automated',
            '5': 'To Be Automated',
            'null': 'No Status'
        };

        const statusColors = {
            '0': 'rgba(220, 53, 69, 0.8)',      // Red - Deleted
            '1': 'rgba(255, 193, 7, 0.8)',      // Yellow - Manual
            '2': 'rgba(52, 58, 64, 0.8)',       // Dark - Obsolete
            '3': 'rgba(220, 53, 69, 0.8)',      // Red - Will Not Automate
            '4': 'rgba(25, 135, 84, 0.8)',      // Green - Automated
            '5': 'rgba(108, 117, 125, 0.8)',    // Gray - To Be Automated
            'null': 'rgba(173, 181, 189, 0.6)'  // Light Gray - No Status
        };

        const breakdown = data.automation_status_breakdown;

        // Filter out statuses with 0 count for cleaner display
        const labels = [];
        const counts = [];
        const colors = [];

        Object.keys(breakdown).forEach(key => {
            if (breakdown[key] > 0) {
                labels.push(statusLabels[key] || key);
                counts.push(breakdown[key]);
                colors.push(statusColors[key] || 'rgba(108, 117, 125, 0.8)');
            }
        });

        // Create the chart
        const ctx = document.getElementById('automationStatusChart').getContext('2d');

        if (automationStatusChart) {
            automationStatusChart.destroy();
        }

        automationStatusChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
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
                        labels: {
                            padding: 15,
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });

        // Create legend with counts
        const legendHtml = `
            <h6 class="mb-3">Status Breakdown</h6>
            <div class="list-group list-group-flush">
                ${labels.map((label, index) => `
                    <div class="list-group-item d-flex justify-content-between align-items-center px-0">
                        <div>
                            <span style="display:inline-block; width:12px; height:12px; background-color:${colors[index]}; border-radius:2px; margin-right:8px;"></span>
                            <small>${label}</small>
                        </div>
                        <span class="badge bg-secondary rounded-pill">${counts[index]}</span>
                    </div>
                `).join('')}
            </div>
            <div class="mt-3 pt-3 border-top">
                <strong>Total Cases: ${data.total_cases}</strong>
            </div>
        `;

        document.getElementById('automation-status-legend').innerHTML = legendHtml;

    } catch (error) {
        console.error('Error loading automation status chart:', error);
        document.getElementById('automation-status-legend').innerHTML =
            '<p class="text-muted">Error loading automation status data</p>';
    }
}

