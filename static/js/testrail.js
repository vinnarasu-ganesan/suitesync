// TestRail page JavaScript

let currentPage = 1;
let currentSortBy = 'case_id';
let currentSortOrder = 'asc';
let currentFilters = {
    suite_id: '',
    section_id: [],
    type_id: '',
    priority_id: '',
    automation_status: '',
    search: ''
};

document.addEventListener('DOMContentLoaded', async () => {
    loadTestrailStats();
    setupSorting();
    setupFilters();
    setupSearch();
    await loadFilterOptions();   // Load filter options
    loadTestrailCases();         // Load the cases

    // Setup clear filters button
    document.getElementById('clear-filters-btn').addEventListener('click', () => {
        clearFilters();
    });
});

async function loadFilterOptions() {
    try {
        const data = await apiCall('/testrail/filters');

        // Populate suite filter
        const suiteFilter = document.getElementById('suite-filter');
        data.suites.forEach(suite => {
            const option = document.createElement('option');
            option.value = suite.value;
            option.textContent = suite.label;
            suiteFilter.appendChild(option);
        });

        // Populate section filter with checkboxes (all sections on initial load)
        populateSectionCheckboxes(data.sections);

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

/**
 * Render section checkboxes from a sections array.
 * Replaces any existing checkboxes inside #section-checkboxes-container.
 * @param {Array}   sections    - array of {value, label} objects
 * @param {boolean} allSelected - if true, every checkbox is pre-checked (default: true)
 */
function populateSectionCheckboxes(sections, allSelected = true) {
    const sectionContainer = document.getElementById('section-checkboxes-container');
    sectionContainer.innerHTML = '';

    if (!sections || sections.length === 0) {
        sectionContainer.innerHTML = '<div class="text-muted small px-2 py-1">No sections available</div>';
        return;
    }

    sections.forEach((section, index) => {
        const checkboxDiv = document.createElement('div');
        checkboxDiv.className = 'form-check';

        const checkbox = document.createElement('input');
        checkbox.className = 'form-check-input section-checkbox';
        checkbox.type = 'checkbox';
        checkbox.value = section.value;
        checkbox.id = `section-${index}`;
        checkbox.checked = allSelected;   // ← pre-check when "All Sections" is active

        const label = document.createElement('label');
        label.className = 'form-check-label';
        label.htmlFor = `section-${index}`;
        label.textContent = section.label;

        checkboxDiv.appendChild(checkbox);
        checkboxDiv.appendChild(label);
        sectionContainer.appendChild(checkboxDiv);
    });
}

/**
 * Re-fetch sections scoped to suiteId (pass '' / null for all suites)
 * and repopulate the dropdown, clearing any prior selection.
 */
async function refreshSectionFilter(suiteId) {
    // Clear current section selections immediately
    currentFilters.section_id = [];
    document.getElementById('section-all').checked = true;

    // Show loading indicator inside the dropdown (clears old checkboxes first)
    const sectionContainer = document.getElementById('section-checkboxes-container');
    sectionContainer.innerHTML = '<div class="text-muted small px-2 py-1"><i class="bi bi-hourglass-split"></i> Loading…</div>';

    // Update label now that old checkboxes are gone
    updateSectionFilterLabel();

    try {
        const url = suiteId ? `/testrail/filters?suite_id=${encodeURIComponent(suiteId)}` : '/testrail/filters';
        const data = await apiCall(url);
        populateSectionCheckboxes(data.sections);
        // Update label again after new checkboxes are in the DOM
        updateSectionFilterLabel();
    } catch (error) {
        console.error('Error refreshing section filter:', error);
        sectionContainer.innerHTML = '<div class="text-danger small px-2 py-1"><i class="bi bi-exclamation-triangle"></i> Error loading sections</div>';
        updateSectionFilterLabel();
    }
}

function setupFilters() {
    // Suite filter – refresh sections whenever the suite changes
    document.getElementById('suite-filter').addEventListener('change', async (e) => {
        currentFilters.suite_id = e.target.value;
        currentPage = 1;
        await refreshSectionFilter(e.target.value);  // repopulate sections first
        loadTestrailStats();
        loadTestrailCases();
    });

    // Section filter - checkbox handling
    setupSectionCheckboxFilter();


    // Type filter
    document.getElementById('type-filter').addEventListener('change', (e) => {
        currentFilters.type_id = e.target.value;
        currentPage = 1;
        loadTestrailStats();
        loadTestrailCases();
    });

    // Priority filter
    document.getElementById('priority-filter').addEventListener('change', (e) => {
        currentFilters.priority_id = e.target.value;
        currentPage = 1;
        loadTestrailStats();
        loadTestrailCases();
    });

    // Automation status filter
    document.getElementById('automation-status-filter').addEventListener('change', (e) => {
        currentFilters.automation_status = e.target.value;
        currentPage = 1;
        loadTestrailStats();
        loadTestrailCases();
    });
}

function setupSectionCheckboxFilter() {
    const dropdown = document.getElementById('section-filter-dropdown');
    const allCheckbox = document.getElementById('section-all');

    // Prevent dropdown from closing when clicking inside
    dropdown.addEventListener('click', (e) => {
        e.stopPropagation();
    });

    // "All Sections" checkbox – checking it resets all individual boxes to checked
    allCheckbox.addEventListener('change', (e) => {
        if (e.target.checked) {
            // Re-check every individual section checkbox
            document.querySelectorAll('.section-checkbox').forEach(cb => { cb.checked = true; });
            currentFilters.section_id = [];
        } else {
            // Uncheck every individual section checkbox
            document.querySelectorAll('.section-checkbox').forEach(cb => { cb.checked = false; });
            currentFilters.section_id = [];
        }
        updateSectionFilterLabel();
        currentPage = 1;
        loadTestrailStats();
        loadTestrailCases();
    });

    // Individual section checkboxes – use event delegation so dynamically-added
    // checkboxes are handled without re-attaching listeners.
    document.addEventListener('change', (e) => {
        if (e.target.classList.contains('section-checkbox')) {
            const allSections    = document.querySelectorAll('.section-checkbox');
            const checkedSections = Array.from(document.querySelectorAll('.section-checkbox:checked'));

            if (checkedSections.length === allSections.length) {
                // All individual sections are checked → back to "All Sections" state
                allCheckbox.checked = true;
                currentFilters.section_id = [];
            } else {
                // Some sections are unchecked → filter to only the checked ones
                allCheckbox.checked = false;
                currentFilters.section_id = checkedSections.map(cb => cb.value);
            }

            updateSectionFilterLabel();
            currentPage = 1;
            loadTestrailStats();
            loadTestrailCases();
        }
    });
}

function updateSectionFilterLabel() {
    const label = document.getElementById('section-filter-label');
    const allSections     = document.querySelectorAll('.section-checkbox');
    const checkedSections = document.querySelectorAll('.section-checkbox:checked');

    // "All Sections" when: no individual checkboxes exist yet, all are checked, or none are checked
    if (allSections.length === 0 ||
        checkedSections.length === allSections.length ||
        checkedSections.length === 0) {
        label.textContent = 'All Sections';
    } else if (checkedSections.length === 1) {
        const sibling = checkedSections[0].nextElementSibling;
        label.textContent = sibling ? sibling.textContent : '1 Section Selected';
    } else {
        label.textContent = `${checkedSections.length} Sections Selected`;
    }
}

function setupSearch() {
    const searchInput = document.getElementById('search-input');
    let debounceTimer;

    searchInput.addEventListener('input', (e) => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            currentFilters.search = e.target.value;
            currentPage = 1;
            loadTestrailStats();
            loadTestrailCases();
        }, 500); // 500ms debounce
    });
}

async function loadTestrailStats() {
    try {
        // Mirror every filter that loadTestrailCases uses so the cards always
        // reflect exactly the same dataset shown in the table.
        const params = new URLSearchParams();
        if (currentFilters.suite_id)
            params.set('suite_id', currentFilters.suite_id);
        if (currentFilters.section_id && currentFilters.section_id.length > 0)
            params.set('section_id', currentFilters.section_id.join(','));
        if (currentFilters.type_id)
            params.set('type_id', currentFilters.type_id);
        if (currentFilters.priority_id)
            params.set('priority_id', currentFilters.priority_id);
        if (currentFilters.automation_status)
            params.set('automation_status', currentFilters.automation_status);
        if (currentFilters.search)
            params.set('search', currentFilters.search);

        const qs = params.toString();
        const data = await apiCall(`/testrail/stats${qs ? '?' + qs : ''}`);

        document.getElementById('total-cases').textContent = data.total_cases || 0;
        document.getElementById('unique-sections').textContent = data.unique_sections || 0;
        document.getElementById('unique-suites').textContent = data.unique_suites || 0;

        // Display automation percentage
        const automationPercentage = data.automation_percentage || 0;
        document.getElementById('automation-percentage').textContent = `${automationPercentage}%`;

        // Optionally change card color based on percentage
        updateAutomationCardColor(automationPercentage);

    } catch (error) {
        console.error('Error loading TestRail stats:', error);
        // Set default values on error
        document.getElementById('total-cases').textContent = '0';
        document.getElementById('unique-sections').textContent = '0';
        document.getElementById('unique-suites').textContent = '0';
        document.getElementById('automation-percentage').textContent = '0%';
    }
}

function updateAutomationCardColor(percentage) {
    const card = document.getElementById('automation-percentage').closest('.card');

    // Remove existing color classes
    card.classList.remove('bg-danger', 'bg-warning', 'bg-success', 'bg-info');

    // Add appropriate color based on percentage
    if (percentage >= 80) {
        card.classList.add('bg-success');
    } else if (percentage >= 50) {
        card.classList.add('bg-info');
    } else if (percentage >= 30) {
        card.classList.add('bg-warning');
    } else {
        card.classList.add('bg-danger');
    }
}

async function loadTestrailCases() {
    console.time('[TestRail] Total load time');
    console.time('[TestRail] API call');

    const tbody = document.getElementById('testrail-cases-tbody');
    tbody.innerHTML = '<tr><td colspan="7" class="text-center"><div class="spinner-border text-primary"></div></td></tr>';

    try {
        // Build query parameters
        let params = `page=${currentPage}&per_page=20&sort_by=${currentSortBy}&sort_order=${currentSortOrder}`;

        if (currentFilters.suite_id) params += `&suite_id=${currentFilters.suite_id}`;
        if (currentFilters.section_id && currentFilters.section_id.length > 0) {
            params += `&section_id=${currentFilters.section_id.join(',')}`;
        }
        if (currentFilters.type_id) params += `&type_id=${currentFilters.type_id}`;
        if (currentFilters.priority_id) params += `&priority_id=${currentFilters.priority_id}`;
        if (currentFilters.automation_status) params += `&automation_status=${currentFilters.automation_status}`;
        if (currentFilters.search) params += `&search=${encodeURIComponent(currentFilters.search)}`;

        const data = await apiCall(`/testrail/cases?${params}`);
        console.timeEnd('[TestRail] API call');
        console.log(`[TestRail] Received ${data.cases.length} cases`);

        // Update filter summary with total count
        updateFilterSummary(data.total);

        if (data.cases.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No TestRail cases found matching the filters.</td></tr>';
            document.getElementById('pagination').innerHTML = '';
            console.timeEnd('[TestRail] Total load time');
            return;
        }

        console.time('[TestRail] HTML generation');
        tbody.innerHTML = data.cases.map(testCase => `
            <tr>
                <td>${formatCaseIdLink(testCase.case_id)}</td>
                <td>${testCase.title}</td>
                <td>${testCase.suite_name || testCase.suite_id || 'N/A'}</td>
                <td>${testCase.section_name || testCase.section_id || 'N/A'}</td>
                <td>${testCase.type_id || 'N/A'}</td>
                <td>${getPriorityBadge(testCase.priority_id)}</td>
                <td>${getAutomationStatusBadge(testCase.automation_status)}</td>
                <td><small>${formatDate(testCase.updated_at)}</small></td>
            </tr>
        `).join('');
        console.timeEnd('[TestRail] HTML generation');

        // Update pagination
        updatePagination(data.pages, currentPage);

        // Update sort indicators
        updateSortIndicators();

        console.timeEnd('[TestRail] Total load time');
    } catch (error) {
        console.error('[TestRail] Error:', error);
        tbody.innerHTML = `
            <tr><td colspan="8" class="text-center text-danger">
                <i class="bi bi-exclamation-triangle"></i> Error loading TestRail cases: ${error.message}
                <br><small>Check the browser console for more details.</small>
            </td></tr>
        `;
        console.timeEnd('[TestRail] Total load time');
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
        '1': '<span class="badge bg-danger">P3 - Critical</span>',
        '2': '<span class="badge bg-secondary">P2 - Low</span>',
        '3': '<span class="badge bg-info">P1 - Medium</span>',
        '4': '<span class="badge bg-warning">P0 - High</span>'
    };

    return priorities[priorityId] || `<span class="badge bg-secondary">${priorityId}</span>`;
}

function getAutomationStatusBadge(automationStatus) {
    if (!automationStatus && automationStatus !== 0) return '<span class="text-muted">N/A</span>';

    const statuses = {
        '0': '<span class="badge bg-danger">Deleted</span>',
        '1': '<span class="badge bg-warning text-dark">Manual</span>',
        '2': '<span class="badge bg-dark">Obsolete</span>',
        '3': '<span class="badge bg-danger">Will Not Automate</span>',
        '4': '<span class="badge bg-success">Automated</span>',
        '5': '<span class="badge bg-secondary">To Be Automated</span>'
    };

    return statuses[String(automationStatus)] || `<span class="badge bg-secondary">${automationStatus}</span>`;
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

// Format Case ID as a clickable link to TestRail
function formatCaseIdLink(caseId) {
    if (!caseId) {
        return '<span class="text-muted">N/A</span>';
    }

    // Remove 'C' prefix if present for the URL
    const numericId = caseId.replace('C', '');

    return `<a href="https://testrail.devx.hpedev.net/index.php?/cases/view/${numericId}"
               target="_blank"
               class="badge bg-info text-decoration-none"
               title="View in TestRail">${caseId}</a>`;
}

// Update filter summary banner
function updateFilterSummary(totalCount) {
    const filterSummary = document.getElementById('filter-summary');
    const filterDescription = document.getElementById('filter-description');

    // Check if any filters are active
    const hasFilters = currentFilters.suite_id ||
                       (currentFilters.section_id && currentFilters.section_id.length > 0) ||
                       currentFilters.type_id || currentFilters.priority_id ||
                       currentFilters.automation_status || currentFilters.search;

    if (hasFilters) {
        let description = `<strong>${totalCount}</strong> case${totalCount !== 1 ? 's' : ''} found`;
        const filters = [];

        // Get filter labels
        if (currentFilters.suite_id) {
            const suiteSelect = document.getElementById('suite-filter');
            const selectedOption = suiteSelect.options[suiteSelect.selectedIndex];
            filters.push(`Suite: <span class="badge bg-primary">${selectedOption.text}</span>`);
        }

        if (currentFilters.section_id && currentFilters.section_id.length > 0) {
            const selectedSections = [];
            currentFilters.section_id.forEach(sectionId => {
                const checkbox = document.querySelector(`.section-checkbox[value="${sectionId}"]`);
                if (checkbox && checkbox.nextElementSibling) {
                    selectedSections.push(`<span class="badge bg-primary">${checkbox.nextElementSibling.textContent}</span>`);
                }
            });
            if (selectedSections.length > 0) {
                filters.push(`Section${currentFilters.section_id.length > 1 ? 's' : ''}: ${selectedSections.join(' ')}`);
            }
        }

        if (currentFilters.type_id) {
            const typeSelect = document.getElementById('type-filter');
            const selectedOption = typeSelect.options[typeSelect.selectedIndex];
            filters.push(`Type: <span class="badge bg-info">${selectedOption.text}</span>`);
        }

        if (currentFilters.priority_id) {
            const priorityLabels = {
                '1': 'P3 - Critical',
                '2': 'P0 - High',
                '3': 'P1 - Medium',
                '4': 'P2 - Low'
            };
            filters.push(`Priority: <span class="badge bg-warning text-dark">${priorityLabels[currentFilters.priority_id]}</span>`);
        }

        if (currentFilters.automation_status) {
            const automationLabels = {
                '0': 'Deleted',
                '1': 'Manual',
                '2': 'Obsolete',
                '3': 'Will Not Automate',
                '4': 'Automated',
                '5': 'To Be Automated'
            };
            filters.push(`Automation: <span class="badge bg-secondary">${automationLabels[currentFilters.automation_status]}</span>`);
        }

        if (currentFilters.search) {
            filters.push(`Search: "<strong>${currentFilters.search}</strong>"`);
        }

        if (filters.length > 0) {
            description += ` with filters: ${filters.join(', ')}`;
        }

        filterDescription.innerHTML = description;
        filterSummary.style.display = 'block';
    } else {
        filterSummary.style.display = 'none';
    }
}

// Clear all filters
async function clearFilters() {
    currentFilters = {
        suite_id: '',
        section_id: [],
        type_id: '',
        priority_id: '',
        automation_status: '',
        search: ''
    };
    currentPage = 1;

    // Reset UI elements
    document.getElementById('suite-filter').value = '';

    // Repopulate sections for "all suites" and reset checkboxes
    await refreshSectionFilter('');

    document.getElementById('type-filter').value = '';
    document.getElementById('priority-filter').value = '';
    document.getElementById('automation-status-filter').value = '';
    document.getElementById('search-input').value = '';

    // Reload stats and cases with cleared filters
    loadTestrailStats();
    loadTestrailCases();
}
