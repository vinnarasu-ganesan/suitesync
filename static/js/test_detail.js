// Test detail page JavaScript

document.addEventListener('DOMContentLoaded', () => {
    loadTestDetail();
});

async function loadTestDetail() {
    const container = document.getElementById('test-detail-container');

    try {
        const test = await apiCall(`/tests/${testId}`);

        let detailHtml = `
            <div class="card mb-4">
                <div class="card-header">
                    <h3 class="mb-0">
                        <i class="bi bi-file-code"></i> ${test.test_name}
                    </h3>
                </div>
                <div class="card-body">
                    <dl class="row">
                        <dt class="col-sm-3">Test ID:</dt>
                        <dd class="col-sm-9"><code>${test.test_id}</code></dd>

                        <dt class="col-sm-3">File:</dt>
                        <dd class="col-sm-9">${test.test_file}</dd>

                        <dt class="col-sm-3">Class:</dt>
                        <dd class="col-sm-9">${test.test_class || '<span class="text-muted">N/A</span>'}</dd>

                        <dt class="col-sm-3">Status:</dt>
                        <dd class="col-sm-9">${getStatusBadge(test.status)}</dd>

                        <dt class="col-sm-3">TestRail ID:</dt>
                        <dd class="col-sm-9">${formatTestRailIds(test.testrail_case_id)}</dd>

                        <dt class="col-sm-3">Created:</dt>
                        <dd class="col-sm-9">${formatDate(test.created_at)}</dd>

                        <dt class="col-sm-3">Updated:</dt>
                        <dd class="col-sm-9">${formatDate(test.updated_at)}</dd>
                    </dl>

                    ${test.description ? `
                        <hr>
                        <h5>Description:</h5>
                        <pre class="bg-light p-3 rounded">${test.description}</pre>
                    ` : ''}
                </div>
            </div>
        `;

        // Add TestRail case details if available
        if (test.testrail_case) {
            detailHtml += `
                <div class="card">
                    <div class="card-header">
                        <h4 class="mb-0">
                            <i class="bi bi-diagram-3"></i> TestRail Case Details
                        </h4>
                    </div>
                    <div class="card-body">
                        <dl class="row">
                            <dt class="col-sm-3">Case ID:</dt>
                            <dd class="col-sm-9">${test.testrail_case.case_id}</dd>

                            <dt class="col-sm-3">Title:</dt>
                            <dd class="col-sm-9">${test.testrail_case.title}</dd>

                            <dt class="col-sm-3">Suite ID:</dt>
                            <dd class="col-sm-9">${test.testrail_case.suite_id || 'N/A'}</dd>

                            <dt class="col-sm-3">Section ID:</dt>
                            <dd class="col-sm-9">${test.testrail_case.section_id || 'N/A'}</dd>

                            <dt class="col-sm-3">Type ID:</dt>
                            <dd class="col-sm-9">${test.testrail_case.type_id || 'N/A'}</dd>

                            <dt class="col-sm-3">Priority ID:</dt>
                            <dd class="col-sm-9">${test.testrail_case.priority_id || 'N/A'}</dd>

                            <dt class="col-sm-3">Last Updated:</dt>
                            <dd class="col-sm-9">${formatDate(test.testrail_case.updated_at)}</dd>
                        </dl>
                    </div>
                </div>
            `;
        }

        container.innerHTML = detailHtml;
    } catch (error) {
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle"></i> Error loading test details: ${error.message}
            </div>
        `;
    }
}

