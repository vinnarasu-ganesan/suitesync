// Dashboard page JavaScript

let syncHistoryChart = null;

document.addEventListener('DOMContentLoaded', () => {
    loadDashboardData();
    loadLastSyncStatus();
    loadRecentTests();
    loadSyncHistory();
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

