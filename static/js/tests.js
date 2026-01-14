// Tests page JavaScript

let currentPage = 1;
let currentStatus = 'active';
let currentSearch = '';
let currentTestrailFilter = '';
let currentMarkerFilter = '';

document.addEventListener('DOMContentLoaded', () => {
    // Check for URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const testrailFilterParam = urlParams.get('testrail_filter');

    if (testrailFilterParam) {
        currentTestrailFilter = testrailFilterParam;
        document.getElementById('testrail-filter').value = testrailFilterParam;
    }

    // Load markers first, then load tests
    loadMarkers();
    loadTests();

    // Set up event listeners
    document.getElementById('search-input').addEventListener('input', (e) => {
        currentSearch = e.target.value;
        currentPage = 1;
        debounce(() => loadTests(), 500)();
    });

    document.getElementById('status-filter').addEventListener('change', (e) => {
        currentStatus = e.target.value;
        currentPage = 1;
        loadTests();
    });

    document.getElementById('marker-filter').addEventListener('change', (e) => {
        currentMarkerFilter = e.target.value;
        currentPage = 1;
        loadTests();
    });

    document.getElementById('testrail-filter').addEventListener('change', (e) => {
        currentTestrailFilter = e.target.value;
        currentPage = 1;
        loadTests();
    });

    // Validate button event listener
    document.getElementById('validate-btn').addEventListener('click', async () => {
        await validateTestRailIds();
    });
});

async function loadMarkers() {
    try {
        const data = await apiCall('/tests/markers');
        const markerFilter = document.getElementById('marker-filter');

        // Clear existing options except the first one
        while (markerFilter.options.length > 1) {
            markerFilter.remove(1);
        }

        // Add all markers from API
        data.markers.forEach(marker => {
            const option = document.createElement('option');
            option.value = marker;
            option.textContent = marker;
            markerFilter.appendChild(option);
        });

        console.log(`[Markers] Loaded ${data.markers.length} unique markers`);
    } catch (error) {
        console.error('[Markers] Error loading markers:', error);
    }
}

async function loadTests() {
    const tbody = document.getElementById('tests-tbody');
    tbody.innerHTML = '<tr><td colspan="7" class="text-center"><div class="spinner-border text-primary"></div></td></tr>';

    try {
        let url = `/tests?page=${currentPage}&per_page=20`;

        if (currentStatus) {
            url += `&status=${currentStatus}`;
        }

        if (currentSearch) {
            url += `&search=${encodeURIComponent(currentSearch)}`;
        }

        const data = await apiCall(url);


        // Apply client-side TestRail filter
        let filteredTests = data.tests;
        if (currentTestrailFilter === 'with') {
            filteredTests = data.tests.filter(t => t.testrail_case_id);
        } else if (currentTestrailFilter === 'without') {
            filteredTests = data.tests.filter(t => !t.testrail_case_id);
        } else if (currentTestrailFilter === 'deleted') {
            filteredTests = data.tests.filter(t => t.testrail_status === 'deleted');
        }

        // Apply marker filter
        if (currentMarkerFilter) {
            filteredTests = filteredTests.filter(test => {
                const markers = test.markers || [];
                return markers.includes(currentMarkerFilter);
            });
        }

        if (filteredTests.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No tests found</td></tr>';
            return;
        }

        tbody.innerHTML = filteredTests.map(test => `
            <tr>
                <td>${formatTestRailIds(test.testrail_case_id)}</td>
                <td>${getTestRailStatusBadge(test.testrail_status, test.testrail_case_id)}</td>
                <td><strong>${test.test_name}</strong></td>
                <td><small class="text-muted">${test.test_file}</small></td>
                <td>${formatMarkers(test.markers)}</td>
                <td>${getStatusBadge(test.status)}</td>
                <td>
                    <a href="/tests/${test.id}" class="btn btn-sm btn-outline-primary">
                        <i class="bi bi-eye"></i> View
                    </a>
                </td>
            </tr>
        `).join('');

        // Update pagination
        updatePagination(data.pages, currentPage);
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-danger">Error loading tests</td></tr>';
    }
}


function updatePagination(totalPages, currentPage) {
    const pagination = document.getElementById('pagination');

    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }

    let paginationHtml = '';

    // Previous button
    paginationHtml += `
        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage - 1}); return false;">Previous</a>
        </li>
    `;

    // Page numbers
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

    // Next button
    paginationHtml += `
        <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage + 1}); return false;">Next</a>
        </li>
    `;

    pagination.innerHTML = paginationHtml;
}

function changePage(page) {
    currentPage = page;
    loadTests();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Debounce function for search
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function getTestRailStatusBadge(status, testrailCaseId) {
    if (!testrailCaseId) {
        return '<span class="badge bg-secondary">No TestRail ID</span>';
    }

    switch(status) {
        case 'valid':
            return '<span class="badge bg-success"><i class="bi bi-check-circle"></i> Valid</span>';
        case 'deleted':
            return '<span class="badge bg-danger"><i class="bi bi-exclamation-triangle"></i> Deleted</span>';
        case 'unknown':
        default:
            return '<span class="badge bg-warning"><i class="bi bi-question-circle"></i> Not Validated</span>';
    }
}

async function validateTestRailIds() {
    console.log('Validate TestRail IDs button clicked');
    const btn = document.getElementById('validate-btn');

    if (!btn) {
        console.error('Validate button not found!');
        return;
    }

    const originalText = btn.innerHTML;

    try {
        // Disable button and show loading
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Validating...';

        console.log('Sending validation request to /api/tests/validate-testrail');

        const response = await fetch('/api/tests/validate-testrail', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        console.log('Response status:', response.status);

        const data = await response.json();
        console.log('Response data:', data);

        if (data.status === 'success') {
            // Show success message
            const message = `Validation complete!\n\nValidated: ${data.validated}\nValid: ${data.valid}\nDeleted TestRail IDs: ${data.deleted}`;
            console.log('Validation successful:', message);
            alert(message);

            // Reload tests to show updated statuses
            console.log('Reloading tests...');
            await loadTests();
        } else {
            const errorMsg = `Error: ${data.message || 'Failed to validate TestRail IDs'}`;
            console.error('Validation failed:', errorMsg);
            alert(errorMsg);
        }
    } catch (error) {
        console.error('Validation error:', error);
        alert('Error validating TestRail IDs. Please check the console for details.');
    } finally {
        // Re-enable button
        console.log('Re-enabling button');
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

// Format markers as colored badges
function formatMarkers(markers) {
    if (!markers || markers.length === 0) {
        return '<span class="text-muted">None</span>';
    }

    // Define color mapping for common markers
    const markerColors = {
        'always': 'primary',
        'run': 'info',
        'smoke': 'success',
        'regression': 'warning',
        'sanity': 'success',
        'integration': 'info',
        'unit': 'secondary',
        'e2e': 'danger',
        'skip': 'secondary',
        'slow': 'warning',
        'fast': 'success',
        'parametrize': 'info',
        'usefixtures': 'info'
    };

    return markers.map(marker => {
        const color = markerColors[marker.toLowerCase()] || 'secondary';
        return `<span class="badge bg-${color} me-1">${marker}</span>`;
    }).join('');
}

// Format TestRail IDs (existing function)
function formatTestRailIds(caseIds) {
    if (!caseIds) {
        return '<span class="text-muted">None</span>';
    }

    // Handle multiple IDs (comma-separated)
    const ids = caseIds.split(',').map(id => id.trim());

    return ids.map(id => {
        return `<a href="https://testrail.devx.hpedev.net/index.php?/cases/view/${id.replace('C', '')}"
                   target="_blank" class="badge bg-info text-decoration-none">${id}</a>`;
    }).join(' ');
}
