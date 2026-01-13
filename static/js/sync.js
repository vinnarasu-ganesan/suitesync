// Sync page JavaScript

let currentPage = 1;

document.addEventListener('DOMContentLoaded', () => {
    loadCurrentStatus();
    loadSyncLogs();

    // Auto-refresh status every 30 seconds
    setInterval(loadCurrentStatus, 30000);
});

async function loadCurrentStatus() {
    try {
        const syncStatus = await apiCall('/sync/status');

        const statusHtml = `
            <dl class="row mb-0">
                <dt class="col-sm-4">Status:</dt>
                <dd class="col-sm-8">${getStatusBadge(syncStatus.status)}</dd>

                <dt class="col-sm-4">Type:</dt>
                <dd class="col-sm-8"><span class="badge bg-secondary">${syncStatus.sync_type}</span></dd>

                <dt class="col-sm-4">Started:</dt>
                <dd class="col-sm-8">${formatDate(syncStatus.started_at)}</dd>

                <dt class="col-sm-4">Completed:</dt>
                <dd class="col-sm-8">${formatDate(syncStatus.completed_at)}</dd>

                <dt class="col-sm-4">Duration:</dt>
                <dd class="col-sm-8">${formatDuration(syncStatus.started_at, syncStatus.completed_at)}</dd>

                <dt class="col-sm-4">Tests Found:</dt>
                <dd class="col-sm-8"><span class="badge bg-primary">${syncStatus.tests_found || 0}</span></dd>

                <dt class="col-sm-4">Tests Synced:</dt>
                <dd class="col-sm-8"><span class="badge bg-success">${syncStatus.tests_synced || 0}</span></dd>

                <dt class="col-sm-4">Tests Failed:</dt>
                <dd class="col-sm-8"><span class="badge bg-danger">${syncStatus.tests_failed || 0}</span></dd>
            </dl>
        `;

        document.getElementById('current-sync-status').innerHTML = statusHtml;
    } catch (error) {
        document.getElementById('current-sync-status').innerHTML = '<p class="text-muted mb-0">No sync operations found.</p>';
    }
}

async function loadSyncLogs() {
    const tbody = document.getElementById('sync-logs-tbody');
    tbody.innerHTML = '<tr><td colspan="10" class="text-center"><div class="spinner-border text-primary"></div></td></tr>';

    try {
        const data = await apiCall(`/sync/logs?page=${currentPage}&per_page=20`);

        if (data.logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="10" class="text-center text-muted">No sync logs found</td></tr>';
            return;
        }

        tbody.innerHTML = data.logs.map(log => `
            <tr>
                <td>${log.id}</td>
                <td><span class="badge bg-secondary">${log.sync_type}</span></td>
                <td>${getStatusBadge(log.status)}</td>
                <td>${log.tests_found || 0}</td>
                <td>${log.tests_synced || 0}</td>
                <td>${log.tests_failed || 0}</td>
                <td>${log.branch || 'N/A'}</td>
                <td><code>${log.commit_hash ? log.commit_hash.substring(0, 8) : 'N/A'}</code></td>
                <td><small>${formatDate(log.started_at)}</small></td>
                <td>${formatDuration(log.started_at, log.completed_at)}</td>
            </tr>
        `).join('');

        // Update pagination
        updatePagination(data.pages, currentPage);
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="10" class="text-center text-danger">Error loading sync logs</td></tr>';
    }
}

function updatePagination(totalPages, currentPage) {
    const pagination = document.getElementById('pagination');

    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }

    let paginationHtml = '';

    paginationHtml += `
        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage - 1}); return false;">Previous</a>
        </li>
    `;

    for (let i = 1; i <= totalPages; i++) {
        if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {
            paginationHtml += `
                <li class="page-item ${i === currentPage ? 'active' : ''}">
                    <a class="page-link" href="#" onclick="changePage(${i}); return false;">${i}</a>
                </li>
            `;
        } else if (i === currentPage - 3 || i === currentPage + 3) {
            paginationHtml += '<li class="page-item disabled"><span class="page-link">...</span></li>';
        }
    }

    paginationHtml += `
        <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage + 1}); return false;">Next</a>
        </li>
    `;

    pagination.innerHTML = paginationHtml;
}

function changePage(page) {
    currentPage = page;
    loadSyncLogs();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

