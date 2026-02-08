// Section Automation Page JavaScript

let sectionsData = [];
let filteredData = [];
let currentSortBy = 'automation_percentage';
let currentSortOrder = 'desc';

document.addEventListener('DOMContentLoaded', async () => {
    console.log('[Section Automation] Page loaded, starting initialization...');
    await loadSectionAutomationData();
    setupFilters();
    setupSearch();
    setupSorting();

    document.getElementById('clear-filters-btn').addEventListener('click', () => {
        clearFilters();
    });

    document.getElementById('export-btn').addEventListener('click', () => {
        exportToCSV();
    });
});

async function loadSectionAutomationData() {
    try {
        console.log('[Section Automation] Fetching data from API...');
        const startTime = Date.now();

        const data = await apiCall('/testrail/section-automation');

        const elapsed = Date.now() - startTime;
        console.log(`[Section Automation] Data fetched in ${elapsed}ms - ${data.sections ? data.sections.length : 0} sections`);

        sectionsData = data.sections || [];
        filteredData = [...sectionsData];
        updateSummaryCards();
        populateSuiteFilter();
        renderTable();
    } catch (error) {
        console.error('[Section Automation] Error loading data:', error);
        showError('Failed to load section automation data. Please refresh the page.');
    }
}

function updateSummaryCards() {
    const totalSections = sectionsData.length;
    let fullyAutomated = 0;
    let partiallyAutomated = 0;
    let totalAutomationPercentage = 0;

    sectionsData.forEach(section => {
        if (section.automation_percentage === 100) {
            fullyAutomated++;
        } else if (section.automation_percentage > 0) {
            partiallyAutomated++;
        }
        totalAutomationPercentage += section.automation_percentage;
    });

    const avgAutomation = totalSections > 0 ? (totalAutomationPercentage / totalSections).toFixed(1) : 0;

    document.getElementById('total-sections').textContent = totalSections;
    document.getElementById('fully-automated').textContent = fullyAutomated;
    document.getElementById('partially-automated').textContent = partiallyAutomated;
    document.getElementById('avg-automation').textContent = `${avgAutomation}%`;
}

function populateSuiteFilter() {
    const suites = [...new Set(sectionsData.map(s => s.suite_name))].sort();
    const suiteFilter = document.getElementById('suite-filter');
    suiteFilter.innerHTML = '<option value="">All Suites</option>';
    suites.forEach(suite => {
        const option = document.createElement('option');
        option.value = suite;
        option.textContent = suite;
        suiteFilter.appendChild(option);
    });
}

function setupFilters() {
    document.getElementById('suite-filter').addEventListener('change', () => applyFilters());
    document.getElementById('automation-filter').addEventListener('change', () => applyFilters());
}

function setupSearch() {
    const searchInput = document.getElementById('search-input');
    let debounceTimer;
    searchInput.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => applyFilters(), 300);
    });
}

function setupSorting() {
    document.querySelectorAll('.sortable').forEach(th => {
        th.addEventListener('click', () => {
            const sortBy = th.dataset.sort;
            if (currentSortBy === sortBy) {
                currentSortOrder = currentSortOrder === 'asc' ? 'desc' : 'asc';
            } else {
                currentSortBy = sortBy;
                currentSortOrder = 'desc';
            }
            sortData();
            renderTable();
            updateSortIndicators();
        });
    });
}

function applyFilters() {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    const selectedSuite = document.getElementById('suite-filter').value;
    const automationLevel = document.getElementById('automation-filter').value;

    filteredData = sectionsData.filter(section => {
        const matchesSearch = !searchTerm || section.section_name.toLowerCase().includes(searchTerm) || section.suite_name.toLowerCase().includes(searchTerm);
        const matchesSuite = !selectedSuite || section.suite_name === selectedSuite;
        let matchesAutomation = true;
        if (automationLevel === 'high') matchesAutomation = section.automation_percentage >= 80;
        else if (automationLevel === 'medium') matchesAutomation = section.automation_percentage >= 50 && section.automation_percentage < 80;
        else if (automationLevel === 'low') matchesAutomation = section.automation_percentage >= 30 && section.automation_percentage < 50;
        else if (automationLevel === 'critical') matchesAutomation = section.automation_percentage < 30;
        return matchesSearch && matchesSuite && matchesAutomation;
    });
    sortData();
    renderTable();
}

function sortData() {
    filteredData.sort((a, b) => {
        let aVal = a[currentSortBy];
        let bVal = b[currentSortBy];
        if (typeof aVal === 'string') {
            aVal = aVal.toLowerCase();
            bVal = bVal.toLowerCase();
        }
        return currentSortOrder === 'asc' ? (aVal > bVal ? 1 : -1) : (aVal < bVal ? 1 : -1);
    });
}

function updateSortIndicators() {
    document.querySelectorAll('.sortable i').forEach(icon => icon.className = 'bi bi-arrow-down-up');
    const currentTh = document.querySelector(`.sortable[data-sort="${currentSortBy}"]`);
    if (currentTh) {
        const icon = currentTh.querySelector('i');
        icon.className = currentSortOrder === 'asc' ? 'bi bi-arrow-up' : 'bi bi-arrow-down';
    }
}

function renderTable() {
    const tbody = document.getElementById('sections-tbody');
    if (filteredData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted py-4"><i class="bi bi-inbox fs-1"></i><p class="mt-2">No sections found.</p></td></tr>';
        return;
    }
    tbody.innerHTML = filteredData.map(section => {
        const percentage = section.automation_percentage;
        const progressBarClass = getProgressBarClass(percentage);
        const badgeClass = getBadgeClass(percentage);
        return `
            <tr class="section-row" onclick="viewSectionDetails('${section.section_id}')">
                <td><strong>${escapeHtml(section.section_name)}</strong><br><small class="text-muted">ID: ${section.section_id}</small></td>
                <td>${escapeHtml(section.suite_name)}</td>
                <td class="text-center"><span class="badge bg-secondary">${section.total_cases}</span></td>
                <td class="text-center"><span class="badge bg-success">${section.automated_count}</span></td>
                <td class="text-center"><span class="badge bg-warning text-dark">${section.manual_count}</span></td>
                <td class="text-center"><span class="badge bg-info">${section.to_be_automated_count}</span></td>
                <td class="text-center"><span class="badge ${badgeClass} automation-badge">${percentage}%</span></td>
                <td><div class="progress"><div class="progress-bar ${progressBarClass}" role="progressbar" style="width: ${percentage}%" aria-valuenow="${percentage}" aria-valuemin="0" aria-valuemax="100">${percentage}%</div></div></td>
            </tr>
        `;
    }).join('');
}

function getProgressBarClass(percentage) {
    if (percentage >= 80) return 'bg-success';
    if (percentage >= 50) return 'bg-info';
    if (percentage >= 30) return 'bg-warning';
    return 'bg-danger';
}

function getBadgeClass(percentage) {
    if (percentage >= 80) return 'bg-success';
    if (percentage >= 50) return 'bg-info';
    if (percentage >= 30) return 'bg-warning';
    return 'bg-danger';
}

function viewSectionDetails(sectionId) {
    window.location.href = `/testrail?section_id=${sectionId}`;
}

function clearFilters() {
    document.getElementById('search-input').value = '';
    document.getElementById('suite-filter').value = '';
    document.getElementById('automation-filter').value = '';
    filteredData = [...sectionsData];
    sortData();
    renderTable();
}

function exportToCSV() {
    if (filteredData.length === 0) {
        alert('No data to export');
        return;
    }
    const headers = ['Section ID', 'Section Name', 'Suite Name', 'Total Cases', 'Automated', 'Manual', 'To Be Automated', 'Will Not Automate', 'Other', 'Automation %'];
    const rows = filteredData.map(section => [section.section_id, section.section_name, section.suite_name, section.total_cases, section.automated_count, section.manual_count, section.to_be_automated_count, section.will_not_automate_count, section.other_count, section.automation_percentage]);
    const csvContent = [headers.join(','), ...rows.map(row => row.map(cell => `"${cell}"`).join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `section_automation_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

function showError(message) {
    const tbody = document.getElementById('sections-tbody');
    tbody.innerHTML = `<tr><td colspan="8" class="text-center text-danger py-4"><i class="bi bi-exclamation-triangle fs-1"></i><p class="mt-2">${escapeHtml(message)}</p></td></tr>`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`/api${endpoint}`, { headers: { 'Content-Type': 'application/json' }, ...options });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}
