// TestRail page JavaScript

let currentPage = 1;
let currentSortBy = 'case_id';
let currentSortOrder = 'asc';
let currentFilters = {
    suite_id: '',
    section_id: '',
    type_id: '',
    priority_id: '',
    search: ''
};
let sectionsMap = {};  // Maps section IDs to names
let suitesMap = {};    // Maps suite IDs to names

document.addEventListener('DOMContentLoaded', async () => {
    loadTestrailStats();
    setupSorting();
    setupFilters();
    setupSearch();
    await loadTestrailNames();  // Wait for names to load first
    await loadFilterOptions();   // Then load filter options (which use the names)
    loadTestrailCases();         // Finally load the cases
});

async function loadTestrailNames() {
    try {
        console.log('Loading TestRail names...');
        const data = await apiCall('/testrail/names');
        sectionsMap = data.sections || {};
        suitesMap = data.suites || {};
        console.log(`✓ Loaded ${Object.keys(sectionsMap).length} sections and ${Object.keys(suitesMap).length} suites`);
        console.log('Sample sections:', Object.entries(sectionsMap).slice(0, 3));
        console.log('Suites:', suitesMap);
    } catch (error) {
        console.error('❌ Error loading TestRail names:', error);
    }
}

function getSectionName(sectionId) {
    if (!sectionId) return 'N/A';
    const name = sectionsMap[sectionId];
    if (!name) {
        console.warn(`Section name not found for ID: ${sectionId}`);
        return `Section ${sectionId}`;
    }
    return name;
}

function getSuiteName(suiteId) {
    if (!suiteId) return 'N/A';
    const name = suitesMap[suiteId];
    if (!name) {
        console.warn(`Suite name not found for ID: ${suiteId}`);
        return `Suite ${suiteId}`;
    }
    return name;
}

async function loadFilterOptions() {
    try {
        const data = await apiCall('/testrail/filters');

        // Populate suite filter
        const suiteFilter = document.getElementById('suite-filter');
        data.suites.forEach(suite => {
            const option = document.createElement('option');
            option.value = suite.value;
            // Use name from suitesMap if available
            const suiteName = suitesMap[suite.value] || suite.label;
            option.textContent = suiteName;
            suiteFilter.appendChild(option);
        });

        // Populate section filter
        const sectionFilter = document.getElementById('section-filter');
        data.sections.forEach(section => {
            const option = document.createElement('option');
            option.value = section.value;
            // Use name from sectionsMap if available, include case count
            const sectionName = sectionsMap[section.value] || `Section ${section.value}`;
            const caseCount = section.label.match(/\((\d+) cases\)/)?.[1] || '';
            option.textContent = caseCount ? `${sectionName} (${caseCount} cases)` : sectionName;
            sectionFilter.appendChild(option);
        });

        // Populate type filter
        const typeFilter = document.getElementById('type-filter');
        data.types.forEach(type => {
            const option = document.createElement('option');
            option.value = type.value;
            option.textContent = type.label;
            typeFilter.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading filter options:', error);
    }
}

function setupFilters() {
    // Suite filter
    document.getElementById('suite-filter').addEventListener('change', (e) => {
        currentFilters.suite_id = e.target.value;
        currentPage = 1;
        loadTestrailCases();
    });

    // Section filter
    document.getElementById('section-filter').addEventListener('change', (e) => {
        currentFilters.section_id = e.target.value;
        currentPage = 1;
        loadTestrailCases();
    });

    // Type filter
    document.getElementById('type-filter').addEventListener('change', (e) => {
        currentFilters.type_id = e.target.value;
        currentPage = 1;
        loadTestrailCases();
    });

    // Priority filter
    document.getElementById('priority-filter').addEventListener('change', (e) => {
        currentFilters.priority_id = e.target.value;
        currentPage = 1;
        loadTestrailCases();
    });
}

function setupSearch() {
    const searchInput = document.getElementById('search-input');
    let debounceTimer;

    searchInput.addEventListener('input', (e) => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            currentFilters.search = e.target.value;
            currentPage = 1;
            loadTestrailCases();
        }, 500); // 500ms debounce
    });
}

async function loadTestrailStats() {
    try {
        const data = await apiCall('/testrail/stats');

        document.getElementById('total-cases').textContent = data.total_cases || 0;
        document.getElementById('unique-sections').textContent = data.unique_sections || 0;
        document.getElementById('unique-suites').textContent = data.unique_suites || 0;

        // Get last sync time from sync status
        try {
            const syncStatus = await apiCall('/sync/status');
            const lastSync = new Date(syncStatus.completed_at || syncStatus.started_at);
            document.getElementById('last-sync').textContent = lastSync.toLocaleDateString();
        } catch (e) {
            document.getElementById('last-sync').textContent = 'N/A';
        }
    } catch (error) {
        console.error('Error loading TestRail stats:', error);
    }
}

async function loadTestrailCases() {
    const tbody = document.getElementById('testrail-cases-tbody');
    tbody.innerHTML = '<tr><td colspan="7" class="text-center"><div class="spinner-border text-primary"></div></td></tr>';

    try {
        // Build query parameters
        let params = `page=${currentPage}&per_page=20&sort_by=${currentSortBy}&sort_order=${currentSortOrder}`;

        if (currentFilters.suite_id) params += `&suite_id=${currentFilters.suite_id}`;
        if (currentFilters.section_id) params += `&section_id=${currentFilters.section_id}`;
        if (currentFilters.type_id) params += `&type_id=${currentFilters.type_id}`;
        if (currentFilters.priority_id) params += `&priority_id=${currentFilters.priority_id}`;
        if (currentFilters.search) params += `&search=${encodeURIComponent(currentFilters.search)}`;

        const data = await apiCall(`/testrail/cases?${params}`);

        if (data.cases.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No TestRail cases found matching the filters.</td></tr>';
            document.getElementById('pagination').innerHTML = '';
            return;
        }

        tbody.innerHTML = data.cases.map(testCase => `
            <tr>
                <td><span class="badge bg-info">${testCase.case_id}</span></td>
                <td>${testCase.title}</td>
                <td>${getSuiteName(testCase.suite_id)}</td>
                <td>${getSectionName(testCase.section_id)}</td>
                <td>${testCase.type_id || 'N/A'}</td>
                <td>${getPriorityBadge(testCase.priority_id)}</td>
                <td><small>${formatDate(testCase.updated_at)}</small></td>
            </tr>
        `).join('');

        // Update pagination
        updatePagination(data.pages, currentPage);

        // Update sort indicators
        updateSortIndicators();
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-danger">Error loading TestRail cases</td></tr>';
    }
}

function setupSorting() {
    document.querySelectorAll('.sortable').forEach(th => {
        th.style.cursor = 'pointer';
        th.addEventListener('click', () => {
            const sortBy = th.dataset.sort;

            // Toggle sort order if clicking same column
            if (currentSortBy === sortBy) {
                currentSortOrder = currentSortOrder === 'asc' ? 'desc' : 'asc';
            } else {
                currentSortBy = sortBy;
                currentSortOrder = 'asc';
            }

            currentPage = 1; // Reset to first page when sorting
            loadTestrailCases();
        });
    });
}

function updateSortIndicators() {
    // Remove all sort indicators
    document.querySelectorAll('.sortable i').forEach(icon => {
        icon.className = 'bi bi-arrow-down-up';
    });

    // Add indicator to current sort column
    const currentTh = document.querySelector(`.sortable[data-sort="${currentSortBy}"]`);
    if (currentTh) {
        const icon = currentTh.querySelector('i');
        if (currentSortOrder === 'asc') {
            icon.className = 'bi bi-arrow-up';
        } else {
            icon.className = 'bi bi-arrow-down';
        }
    }
}

function getPriorityBadge(priorityId) {
    if (!priorityId) return '<span class="text-muted">N/A</span>';

    const priorities = {
        '1': '<span class="badge bg-danger">Critical</span>',
        '2': '<span class="badge bg-warning">High</span>',
        '3': '<span class="badge bg-info">Medium</span>',
        '4': '<span class="badge bg-secondary">Low</span>'
    };

    return priorities[priorityId] || `<span class="badge bg-secondary">${priorityId}</span>`;
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
    loadTestrailCases();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

