// Tests page JavaScript

let currentPage = 1;
let currentStatus = 'active';
let currentSearch = '';
let currentTestrailFilter = '';

document.addEventListener('DOMContentLoaded', () => {
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

    document.getElementById('testrail-filter').addEventListener('change', (e) => {
        currentTestrailFilter = e.target.value;
        currentPage = 1;
        loadTests();
    });
});

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
        }

        if (filteredTests.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No tests found</td></tr>';
            return;
        }

        tbody.innerHTML = filteredTests.map(test => `
            <tr>
                <td><small><code>${test.test_id}</code></small></td>
                <td>${formatTestRailIds(test.testrail_case_id)}</td>
                <td><strong>${test.test_name}</strong></td>
                <td><small class="text-muted">${test.test_file}</small></td>
                <td>${test.test_class || '<span class="text-muted">N/A</span>'}</td>
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

