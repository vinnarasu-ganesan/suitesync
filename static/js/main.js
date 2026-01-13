// Common utility functions

// Format date
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString();
}

// Format duration
function formatDuration(startDate, endDate) {
    if (!startDate || !endDate) return 'N/A';
    const start = new Date(startDate);
    const end = new Date(endDate);
    const durationMs = end - start;
    const seconds = Math.floor(durationMs / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) {
        return `${hours}h ${minutes % 60}m`;
    } else if (minutes > 0) {
        return `${minutes}m ${seconds % 60}s`;
    } else {
        return `${seconds}s`;
    }
}

// Get status badge
function getStatusBadge(status) {
    const badges = {
        'active': '<span class="badge bg-success">Active</span>',
        'archived': '<span class="badge bg-secondary">Archived</span>',
        'success': '<span class="badge bg-success">Success</span>',
        'failed': '<span class="badge bg-danger">Failed</span>',
        'in_progress': '<span class="badge bg-warning">In Progress</span>'
    };
    return badges[status] || `<span class="badge bg-secondary">${status}</span>`;
}

// API call helper
async function apiCall(endpoint) {
    try {
        const response = await fetch(`/api${endpoint}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

// Show toast notification
function showToast(title, message, type = 'info') {
    // Simple alert for now, can be replaced with Bootstrap toast
    const alertClass = type === 'success' ? 'alert-success' :
                      type === 'danger' ? 'alert-danger' :
                      type === 'warning' ? 'alert-warning' : 'alert-info';

    const toast = document.createElement('div');
    toast.className = `alert ${alertClass} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    toast.style.zIndex = '9999';
    toast.innerHTML = `
        <strong>${title}</strong><br>${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 5000);
}

// Trigger sync
async function triggerSync() {
    if (!confirm('Start synchronization? This may take a few minutes.')) {
        return;
    }

    showToast('Sync Started', 'Synchronization in progress...', 'info');

    try {
        const result = await apiCall('/sync', {
            method: 'POST'
        });

        if (result.status === 'success') {
            showToast('Sync Completed', result.message || 'Synchronization completed successfully', 'success');

            // Reload page after a short delay
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        } else {
            showToast('Sync Failed', result.message || 'Synchronization failed', 'danger');
        }
    } catch (error) {
        console.error('Sync error:', error);
        showToast('Sync Error', 'Failed to start synchronization', 'danger');
    }
}

// Pagination helper
function createPagination(total, perPage, currentPage, onPageChange) {
    const totalPages = Math.ceil(total / perPage);
    const pagination = document.createElement('nav');

    let html = '<ul class="pagination">';

    // Previous button
    html += `<li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
        <a class="page-link" href="#" data-page="${currentPage - 1}">Previous</a>
    </li>`;

    // Page numbers
    for (let i = 1; i <= totalPages; i++) {
        if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {
            html += `<li class="page-item ${i === currentPage ? 'active' : ''}">
                <a class="page-link" href="#" data-page="${i}">${i}</a>
            </li>`;
        } else if (i === currentPage - 3 || i === currentPage + 3) {
            html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
        }
    }

    // Next button
    html += `<li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
        <a class="page-link" href="#" data-page="${currentPage + 1}">Next</a>
    </li>`;

    html += '</ul>';
    pagination.innerHTML = html;

    // Add click handlers
    pagination.querySelectorAll('a.page-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = parseInt(link.dataset.page);
            if (page > 0 && page <= totalPages) {
                onPageChange(page);
            }
        });
    });

    return pagination;
}

// Format TestRail IDs (handles single or multiple comma-separated IDs)
function formatTestRailIds(testrailIds) {
    if (!testrailIds) {
        return '<span class="text-muted">N/A</span>';
    }

    // Check if multiple IDs (comma-separated)
    if (testrailIds.includes(',')) {
        const ids = testrailIds.split(',').map(id => id.trim());
        return ids.map(id => `<span class="badge bg-info me-1">${id}</span>`).join('');
    } else {
        // Single ID
        return `<span class="badge bg-info">${testrailIds}</span>`;
    }
}
