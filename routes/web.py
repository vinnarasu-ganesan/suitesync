from flask import Blueprint, render_template

web_bp = Blueprint('web', __name__)


@web_bp.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')


@web_bp.route('/tests')
def tests():
    """Tests listing page."""
    return render_template('tests.html')


@web_bp.route('/tests/<int:test_id>')
def test_detail(test_id):
    """Test detail page."""
    return render_template('test_detail.html', test_id=test_id)


@web_bp.route('/sync')
def sync_page():
    """Sync management page."""
    return render_template('sync.html')


@web_bp.route('/testrail')
def testrail():
    """TestRail cases page."""
    return render_template('testrail.html')


@web_bp.route('/diagnostic')
def diagnostic():
    """Diagnostic page to test API connectivity."""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>SuiteSync Diagnostic</title></head>
    <body>
        <h1>SuiteSync Diagnostic</h1>
        <div id="results"></div>
        <script>
            const results = document.getElementById('results');
            results.innerHTML += '<h2>1. Testing API...</h2>';
            
            fetch('/api/tests/stats')
                .then(response => response.json())
                .then(data => {
                    results.innerHTML += '<p>OK API Stats: Total tests = ' + data.total_tests + '</p>';
                })
                .catch(error => {
                    results.innerHTML += '<p>ERROR API: ' + error + '</p>';
                });
            
            fetch('/api/tests?per_page=5')
                .then(response => response.json())
                .then(data => {
                    results.innerHTML += '<p>OK API Tests: Found ' + data.total + ' tests</p>';
                    if (data.tests && data.tests.length > 0) {
                        results.innerHTML += '<p>Sample: ' + data.tests[0].test_name + '</p>';
                    }
                })
                .catch(error => {
                    results.innerHTML += '<p>ERROR Tests API: ' + error + '</p>';
                });
        </script>
    </body>
    </html>
    """


@web_bp.route('/simple-test')
def simple_test():
    """Simple test page with inline JavaScript."""
    return render_template('simple_test.html')
