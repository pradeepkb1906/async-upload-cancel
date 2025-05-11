import http.server
import socketserver
import urllib.request
import urllib.error
import urllib.parse
import json
import base64
import ssl
import os
import threading
import webbrowser
import time
import socket

# Global variables to store session data
SONAR_URL = ""
AUTH_HEADER = ""
PROJECT_KEY = ""

# Define HTML templates
LOGIN_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SonarQube Metrics Viewer - Login</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            color: #0066CC;
            border-bottom: 2px solid #0066CC;
            padding-bottom: 10px;
        }
        form {
            background: #f9f9f9;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
        }
        input[type="text"],
        input[type="password"],
        input[type="url"] {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 16px;
        }
        button {
            background: #0066CC;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
        }
        button:hover {
            background: #005bb5;
        }
        .error {
            color: #e74c3c;
            background: #fadbd8;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 15px;
            display: none;
        }
        .info-text {
            margin-top: 10px;
            font-size: 14px;
            color: #666;
        }
    </style>
</head>
<body>
    <h1>SonarQube Metrics Viewer</h1>
    <div id="error-message" class="error"></div>
    <form id="login-form" action="/login" method="post">
        <div class="form-group">
            <label for="sonar-url">SonarQube URL:</label>
            <input type="url" id="sonar-url" name="sonar-url" placeholder="https://your-sonarqube-instance.com">
            <div class="info-text">The URL of your SonarQube or SonarCloud instance</div>
        </div>
        <div class="form-group">
            <label for="project-key">Project Key:</label>
            <input type="text" id="project-key" name="project-key" placeholder="project-key">
            <div class="info-text">The key of the project you want to analyze</div>
        </div>
        <div class="form-group">
            <label for="token">Access Token:</label>
            <input type="password" id="token" name="token" placeholder="Enter your SonarQube access token">
            <div class="info-text">Your access token from User Account > Security > Generate Tokens</div>
        </div>
        <button type="submit">View Metrics</button>
    </form>

    <script>
        document.getElementById('login-form').addEventListener('submit', function(e) {
            e.preventDefault();
            const errorMessage = document.getElementById('error-message');
            errorMessage.style.display = 'none';
            
            // Get form data
            const formData = new FormData(this);
            
            // Send form data to server
            fetch('/login', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.href = '/metrics';
                } else {
                    errorMessage.textContent = data.message;
                    errorMessage.style.display = 'block';
                }
            })
            .catch(error => {
                errorMessage.textContent = 'An error occurred. Please try again.';
                errorMessage.style.display = 'block';
            });
        });
    </script>
</body>
</html>
"""

METRICS_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SonarQube Metrics: {project_name}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            background: #0066CC;
            color: white;
            padding: 20px;
            margin-bottom: 30px;
        }
        .header-content {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        h1 {
            margin: 0;
        }
        .back-button {
            background: transparent;
            border: 2px solid white;
            color: white;
            padding: 8px 15px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 600;
            text-decoration: none;
        }
        .back-button:hover {
            background: rgba(255,255,255,0.1);
        }
        .dashboard {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }
        @media (max-width: 1024px) {
            .dashboard {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        @media (max-width: 768px) {
            .dashboard {
                grid-template-columns: 1fr;
            }
        }
        .card {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px;
            display: flex;
            flex-direction: column;
        }
        .card h2 {
            margin-top: 0;
            color: #0066CC;
            font-size: 18px;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }
        .quality-gate {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: 600;
            margin-top: 5px;
        }
        .quality-gate.pass {
            background-color: #d4edda;
            color: #155724;
        }
        .quality-gate.fail {
            background-color: #f8d7da;
            color: #721c24;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }
        .metric:last-child {
            border-bottom: none;
        }
        .metric-name {
            font-weight: 500;
        }
        .metric-value {
            font-weight: 600;
            font-size: 18px;
        }
        .metric-value.good {
            color: #155724;
        }
        .metric-value.warning {
            color: #856404;
        }
        .metric-value.critical {
            color: #721c24;
        }
        .metric-value.neutral {
            color: #0066CC;
        }
        .rating {
            display: inline-block;
            width: 28px;
            height: 28px;
            line-height: 28px;
            text-align: center;
            border-radius: 50%;
            color: white;
            font-weight: 600;
        }
        .rating.A {
            background-color: #27ae60;
        }
        .rating.B {
            background-color: #2ecc71;
        }
        .rating.C {
            background-color: #f1c40f;
        }
        .rating.D {
            background-color: #e67e22;
        }
        .rating.E {
            background-color: #e74c3c;
        }
        .chart-container {
            height: 250px;
            margin-top: auto;
        }
        .server-info {
            margin-bottom: 10px;
            font-size: 14px;
            color: rgba(255,255,255,0.8);
        }
    </style>
</head>
<body>
    <header>
        <div class="header-content">
            <div>
                <h1>{project_name} Metrics</h1>
                <div class="server-info">Server: {server_url}</div>
            </div>
            <a href="/" class="back-button">Back to Login</a>
        </div>
    </header>
    
    <div class="container">
        <div class="dashboard">
            <!-- Quality Management Card -->
            <div class="card">
                <h2>Quality Management</h2>
                <div class="quality-gate {gate_class}">Quality Gate: {gate_status}</div>
                <div class="metric">
                    <span class="metric-name">Lines of Code</span>
                    <span class="metric-value neutral">{ncloc}</span>
                </div>
                <div class="metric">
                    <span class="metric-name">Duplications</span>
                    <span class="metric-value {duplication_class}">{duplications}%</span>
                </div>
                <div class="metric">
                    <span class="metric-name">Coverage</span>
                    <span class="metric-value {coverage_class}">{coverage}%</span>
                </div>
                <div class="chart-container">
                    <canvas id="qualityChart"></canvas>
                </div>
            </div>
            
            <!-- Bug Detection Card -->
            <div class="card">
                <h2>Bug Detection</h2>
                <div class="metric">
                    <span class="metric-name">Reliability Rating</span>
                    <span class="rating {reliability_rating}">{reliability_rating}</span>
                </div>
                <div class="metric">
                    <span class="metric-name">Bugs</span>
                    <span class="metric-value {bugs_class}">{bugs}</span>
                </div>
                <div class="metric">
                    <span class="metric-name">Bugs per 1k Lines</span>
                    <span class="metric-value {bugs_density_class}">{bugs_density}</span>
                </div>
                <div class="chart-container">
                    <canvas id="bugsChart"></canvas>
                </div>
            </div>
            
            <!-- Security Vulnerability Detection Card -->
            <div class="card">
                <h2>Security Vulnerability Detection</h2>
                <div class="metric">
                    <span class="metric-name">Security Rating</span>
                    <span class="rating {security_rating}">{security_rating}</span>
                </div>
                <div class="metric">
                    <span class="metric-name">Vulnerabilities</span>
                    <span class="metric-value {vulnerabilities_class}">{vulnerabilities}</span>
                </div>
                <div class="metric">
                    <span class="metric-name">Security Hotspots</span>
                    <span class="metric-value {hotspots_class}">{hotspots}</span>
                </div>
                <div class="chart-container">
                    <canvas id="securityChart"></canvas>
                </div>
            </div>
            
            <!-- Technical Debt Tracking Card -->
            <div class="card">
                <h2>Technical Debt Tracking</h2>
                <div class="metric">
                    <span class="metric-name">Technical Debt</span>
                    <span class="metric-value neutral">{debt_time}</span>
                </div>
                <div class="metric">
                    <span class="metric-name">Technical Debt Ratio</span>
                    <span class="metric-value {debt_ratio_class}">{debt_ratio}%</span>
                </div>
                <div class="metric">
                    <span class="metric-name">Code Smells</span>
                    <span class="metric-value {code_smells_class}">{code_smells}</span>
                </div>
                <div class="chart-container">
                    <canvas id="techDebtChart"></canvas>
                </div>
            </div>
            
            <!-- Maintainability Analysis Card -->
            <div class="card">
                <h2>Maintainability Analysis</h2>
                <div class="metric">
                    <span class="metric-name">Maintainability Rating</span>
                    <span class="rating {maintainability_rating}">{maintainability_rating}</span>
                </div>
                <div class="metric">
                    <span class="metric-name">Complexity</span>
                    <span class="metric-value neutral">{complexity}</span>
                </div>
                <div class="metric">
                    <span class="metric-name">Cognitive Complexity</span>
                    <span class="metric-value neutral">{cognitive_complexity}</span>
                </div>
                <div class="chart-container">
                    <canvas id="maintainabilityChart"></canvas>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Charts initialization
        window.onload = function() {
            // Quality Chart
            const qualityCtx = document.getElementById('qualityChart').getContext('2d');
            new Chart(qualityCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Duplications', 'Coverage', 'Other'],
                    datasets: [{
                        data: [{duplications}, {coverage}, Math.max(0, 100 - {duplications} - {coverage})],
                        backgroundColor: ['#f1c40f', '#2ecc71', '#ecf0f1']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
            
            // Bugs Chart
            const bugsCtx = document.getElementById('bugsChart').getContext('2d');
            new Chart(bugsCtx, {
                type: 'bar',
                data: {
                    labels: ['Bugs'],
                    datasets: [{
                        label: 'Count',
                        data: [{bugs}],
                        backgroundColor: '#e74c3c'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                precision: 0
                            }
                        }
                    }
                }
            });
            
            // Security Chart
            const securityCtx = document.getElementById('securityChart').getContext('2d');
            new Chart(securityCtx, {
                type: 'bar',
                data: {
                    labels: ['Vulnerabilities', 'Hotspots'],
                    datasets: [{
                        label: 'Count',
                        data: [{vulnerabilities}, {hotspots}],
                        backgroundColor: ['#e74c3c', '#f39c12']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                precision: 0
                            }
                        }
                    }
                }
            });
            
            // Tech Debt Chart
            const techDebtCtx = document.getElementById('techDebtChart').getContext('2d');
            new Chart(techDebtCtx, {
                type: 'pie',
                data: {
                    labels: ['Technical Debt', 'Clean Code'],
                    datasets: [{
                        data: [{debt_ratio}, Math.max(0, 100 - {debt_ratio})],
                        backgroundColor: ['#e74c3c', '#2ecc71']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
            
            // Maintainability Chart
            const maintainabilityCtx = document.getElementById('maintainabilityChart').getContext('2d');
            new Chart(maintainabilityCtx, {
                type: 'radar',
                data: {
                    labels: ['Code Smells', 'Complexity', 'Cognitive Complexity'],
                    datasets: [{
                        label: 'Values',
                        data: [
                            {code_smells_normalized}, 
                            {complexity_normalized}, 
                            {cognitive_complexity_normalized}
                        ],
                        fill: true,
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        borderColor: 'rgb(54, 162, 235)',
                        pointBackgroundColor: 'rgb(54, 162, 235)',
                        pointBorderColor: '#fff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: 'rgb(54, 162, 235)'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        r: {
                            angleLines: {
                                display: true
                            },
                            suggestedMin: 0,
                            suggestedMax: 100
                        }
                    }
                }
            });
        };
    </script>
</body>
</html>
"""

class SonarRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(LOGIN_PAGE.encode())
        elif self.path == '/metrics':
            self.send_metrics_page()
        else:
            self.send_error(404, "Page not found")
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/login':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Parse form data
            form_data = self.parse_form_data(post_data)
            
            # Get form fields
            sonar_url = form_data.get('sonar-url', [''])[0]
            project_key = form_data.get('project-key', [''])[0]
            token = form_data.get('token', [''])[0]
            
            # Process login
            result = self.process_login(sonar_url, project_key, token)
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
    
    def parse_form_data(self, post_data):
        """Parse form data"""
        form_data = {}
        
        # Convert bytes to string for form data
        try:
            # Try to decode as URL-encoded form data
            decoded_data = post_data.decode('utf-8')
            
            # Check if it's FormData object from JavaScript
            if 'Content-Disposition: form-data;' in decoded_data:
                # It's multipart/form-data
                boundary = self.headers['Content-Type'].split('=')[1]
                parts = decoded_data.split('--' + boundary)
                
                for part in parts:
                    if 'Content-Disposition: form-data;' in part:
                        # Extract field name
                        name_start = part.find('name="') + 6
                        name_end = part.find('"', name_start)
                        field_name = part[name_start:name_end]
                        
                        # Extract value (after the double newline)
                        value_start = part.find('\r\n\r\n') + 4
                        value_end = part.rfind('\r\n')
                        value = part[value_start:value_end]
                        
                        form_data[field_name] = [value]
            else:
                # It's regular form data (application/x-www-form-urlencoded)
                fields = decoded_data.split('&')
                for field in fields:
                    if '=' in field:
                        key, value = field.split('=', 1)
                        form_data[key] = [urllib.parse.unquote_plus(value)]
        except Exception as e:
            print(f"Error parsing form data: {e}")
        
        return form_data
    
    def process_login(self, sonar_url, project_key, token):
        """Process login and verify project exists"""
        global SONAR_URL, AUTH_HEADER, PROJECT_KEY
        
        # Remove trailing slash if present
        if sonar_url.endswith('/'):
            sonar_url = sonar_url[:-1]
        
        # Validate required fields
        if not sonar_url:
            return {
                'success': False,
                'message': 'SonarQube URL is required.'
            }
            
        if not project_key:
            return {
                'success': False,
                'message': 'Project key is required.'
            }
            
        if not token:
            return {
                'success': False,
                'message': 'Access token is required for authentication.'
            }
        
        # Store values
        SONAR_URL = sonar_url
        PROJECT_KEY = project_key
        
        # Create auth header with token
        AUTH_HEADER = f"Basic {base64.b64encode(f'{token}:'.encode()).decode()}"
        
        try:
            # Test connection by fetching project
            project_info = self.fetch_project_info(sonar_url, AUTH_HEADER, project_key)
            
            if not project_info:
                return {
                    'success': False,
                    'message': f'Project with key "{project_key}" not found or you do not have access to it.'
                }
            
            return {
                'success': True,
                'message': 'Login successful'
            }
        except urllib.error.HTTPError as e:
            error_msg = f"HTTP Error: {e.code}"
            if e.code == 401:
                error_msg = "Authentication failed. Please check your token."
            elif e.code == 403:
                error_msg = "Authorization failed. Check your token and project permissions."
            elif e.code == 404:
                error_msg = f"Project not found. Check if the project key '{project_key}' is correct."
            
            # Try to get more detailed error message from response
            try:
                error_content = e.read().decode('utf-8')
                error_json = json.loads(error_content)
                if 'message' in error_json:
                    error_msg += f" - {error_json['message']}"
            except:
                pass
                
            return {
                'success': False,
                'message': error_msg
            }
        except Exception as e:
            print(f"Login error: {str(e)}")
            return {
                'success': False,
                'message': f'Error connecting to SonarQube: {str(e)}'
            }
    
    def fetch_project_info(self, sonar_url, auth_header, project_key):
        """Fetch basic project info to verify it exists"""
        url = f"{sonar_url}/api/components/show?component={project_key}"
        print(f"Fetching project info from: {url}")
        
        req = urllib.request.Request(url)
        req.add_header("Authorization", auth_header)
        
        # Disable SSL verification for simplicity
        context = ssl._create_unverified_context()
        
        try:
            response = urllib.request.urlopen(req, context=context)
            response_data = response.read().decode('utf-8')
            data = json.loads(response_data)
            return data.get('component')
        except Exception as e:
            print(f"Error fetching project info: {e}")
            raise
    
    def send_metrics_page(self):
        """Send metrics page for the project"""
        global SONAR_URL, AUTH_HEADER, PROJECT_KEY
        
        if not SONAR_URL or not AUTH_HEADER or not PROJECT_KEY:
            # Redirect to login if no session
            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()
            return
        
        try:
            # Fetch project info for name
            project_info = self.fetch_project_info(SONAR_URL, AUTH_HEADER, PROJECT_KEY)
            project_name = project_info.get('name', PROJECT_KEY)
            
            # Fetch project metrics
            metrics = self.fetch_metrics(SONAR_URL, AUTH_HEADER, PROJECT_KEY)
            
            # Generate HTML
            html = self.generate_metrics_html(project_name, metrics)
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html.encode())
            
        except Exception as e:
            print(f"Error fetching metrics: {str(e)}")
            self.send_error(500, f"Error fetching metrics: {str(e)}")
    
    def fetch_metrics(self, sonar_url, auth_header, project_key):
        """Fetch metrics for a project"""
        # Define the metrics we want to fetch
        metrics = [
            # Quality Management
            "ncloc", "duplicated_lines_density", "coverage",
            
            # Bug Detection
            "bugs", "reliability_rating",
            
            # Security Vulnerabilities
            "vulnerabilities", "security_rating", "security_hotspots",
            
            # Technical Debt
            "sqale_index", "sqale_debt_ratio", "code_smells",
            
            # Maintainability
            "sqale_rating", "complexity", "cognitive_complexity"
        ]
        
        metrics_param = ",".join(metrics)
        
        # Fetch measures
        measures_url = f"{sonar_url}/api/measures/component?component={project_key}&metricKeys={metrics_param}"
        print(f"Fetching metrics from: {measures_url}")
        
        measures_req = urllib.request.Request(measures_url)
        measures_req.add_header("Authorization", auth_header)
        
        # Fetch quality gate
        gate_url = f"{sonar_url}/api/qualitygates/project_status?projectKey={project_key}"
        print(f"Fetching quality gate from: {gate_url}")
        
        gate_req = urllib.request.Request(gate_url)
        gate_req.add_header("Authorization", auth_header)
        
        # Disable SSL verification for simplicity
        context = ssl._create_unverified_context()
        
        try:
            # Fetch measures data
            measures_response = urllib.request.urlopen(measures_req, context=context)
            measures_data = json.loads(measures_response.read().decode())
            
            # Fetch quality gate data
            gate_response = urllib.request.urlopen(gate_req, context=context)
            gate_data = json.loads(gate_response.read().decode())
            
            # Extract measures
            measures = {}
            for measure in measures_data.get('component', {}).get('measures', []):
                measures[measure.get('metric')] = measure.get('value')
            
            # Extract quality gate status
            quality_gate = gate_data.get('projectStatus', {}).get('status', 'NONE')
            
            # Add quality gate to measures
            measures['quality_gate'] = quality_gate
            
            return measures
            
        except urllib.error.HTTPError as e:
            print(f"HTTP Error when fetching metrics: {e.code}")
            print(f"Response: {e.read().decode('utf-8')}")
            raise
        except json.JSONDecodeError as e:
            print(f"JSON decode error when fetching metrics: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error when fetching metrics: {e}")
            raise
    
    def format_time(self, minutes):
        """Format time from minutes to hours and minutes"""
        if not minutes:
            return "0m"
        
        try:
            mins = int(minutes)
            hours = mins // 60
            remaining_mins = mins % 60
            
            if hours > 0:
                return f"{hours}h {remaining_mins}m" if remaining_mins > 0 else f"{hours}h"
            else:
                return f"{mins}m"
        except:
            return minutes
    
    def format_rating(self, rating):
        """Format SonarQube rating (1=A, 2=B, etc.)"""
        ratings = {'1': 'A', '2': 'B', '3': 'C', '4': 'D', '5': 'E'}
        return ratings.get(rating, rating)
    
    def get_class_for_value(self, metric, value):
        """Get CSS class based on metric value"""
        if metric == "coverage":
            try:
                coverage = float(value)
                if coverage >= 80:
                    return "good"
                elif coverage >= 50:
                    return "warning"
                else:
                    return "critical"
            except:
                return "neutral"
        
        elif metric == "duplications":
            try:
                duplication = float(value)
                if duplication <= 3:
                    return "good"
                elif duplication <= 10:
                    return "warning"
                else:
                    return "critical"
            except:
                return "neutral"
        
        elif metric in ["bugs", "vulnerabilities", "hotspots"]:
            try:
                count = int(value)
                if count == 0:
                    return "good"
                elif count < 5:
                    return "warning"
                else:
                    return "critical"
            except:
                return "neutral"
        
        elif metric == "code_smells":
            try:
                count = int(value)
                if count < 10:
                    return "good"
                elif count < 50:
                    return "warning"
                else:
                    return "critical"
            except:
                return "neutral"
        
        elif metric == "debt_ratio":
            try:
                ratio = float(value)
                if ratio < 5:
                    return "good"
                elif ratio < 20:
                    return "warning"
                else:
                    return "critical"
            except:
                return "neutral"
                
        return "neutral"
    
    def generate_metrics_html(self, project_name, metrics):
        """Generate HTML for metrics dashboard"""
        # Extract metrics with default values for missing ones
        quality_gate = metrics.get('quality_gate', 'NONE')
        ncloc = metrics.get('ncloc', '0')
        duplications = metrics.get('duplicated_lines_density', '0')
        coverage = metrics.get('coverage', '0')
        bugs = metrics.get('bugs', '0')
        reliability_rating = self.format_rating(metrics.get('reliability_rating', '0'))
        vulnerabilities = metrics.get('vulnerabilities', '0')
        security_rating = self.format_rating(metrics.get('security_rating', '0'))
        hotspots = metrics.get('security_hotspots', '0')
        debt_minutes = metrics.get('sqale_index', '0')
        debt_ratio = metrics.get('sqale_debt_ratio', '0')
        code_smells = metrics.get('code_smells', '0')
        maintainability_rating = self.format_rating(metrics.get('sqale_rating', '0'))
        complexity = metrics.get('complexity', '0')
        cognitive_complexity = metrics.get('cognitive_complexity', '0')
        
        # Calculate normalized values for radar chart (0-100 scale)
        try:
            code_smells_normalized = min(100, int(code_smells) / 5)
        except:
            code_smells_normalized = 0
            
        try:
            complexity_normalized = min(100, int(complexity) / 10)
        except:
            complexity_normalized = 0
            
        try:
            cognitive_complexity_normalized = min(100, int(cognitive_complexity) / 10)
        except:
            cognitive_complexity_normalized = 0
        
        # Format values
        debt_time = self.format_time(debt_minutes)
        
        # Calculate bugs density per 1000 lines
        try:
            bugs_density = round((int(bugs) * 1000) / max(1, int(ncloc)), 2)
        except:
            bugs_density = 0
        
        # Get CSS classes
        gate_class = "pass" if quality_gate == "OK" else "fail"
        duplication_class = self.get_class_for_value("duplications", duplications)
        coverage_class = self.get_class_for_value("coverage", coverage)
        bugs_class = self.get_class_for_value("bugs", bugs)
        bugs_density_class = self.get_class_for_value("bugs", bugs)
        vulnerabilities_class = self.get_class_for_value("vulnerabilities", vulnerabilities)
        hotspots_class = self.get_class_for_value("hotspots", hotspots)
        debt_ratio_class = self.get_class_for_value("debt_ratio", debt_ratio)
        code_smells_class = self.get_class_for_value("code_smells", code_smells)
        
        # Format the HTML template
        html = METRICS_TEMPLATE.format(
            project_name=project_name,
            server_url=SONAR_URL,
            gate_status="Passed" if quality_gate == "OK" else "Failed",
            gate_class=gate_class,
            ncloc=ncloc,
            duplications=duplications,
            duplication_class=duplication_class,
            coverage=coverage,
            coverage_class=coverage_class,
            bugs=bugs,
            bugs_class=bugs_class,
            bugs_density=bugs_density,
            bugs_density_class=bugs_density_class,
            reliability_rating=reliability_rating,
            vulnerabilities=vulnerabilities,
            vulnerabilities_class=vulnerabilities_class,
            security_rating=security_rating,
            hotspots=hotspots,
            hotspots_class=hotspots_class,
            debt_time=debt_time,
            debt_ratio=debt_ratio,
            debt_ratio_class=debt_ratio_class,
            code_smells=code_smells,
            code_smells_class=code_smells_class,
            maintainability_rating=maintainability_rating,
            complexity=complexity,
            cognitive_complexity=cognitive_complexity,
            code_smells_normalized=code_smells_normalized,
            complexity_normalized=complexity_normalized,
            cognitive_complexity_normalized=cognitive_complexity_normalized
        )
        
        return html

def open_browser(port):
    """Open browser after a short delay"""
    time.sleep(1.5)
    webbrowser.open(f"http://localhost:{port}")
    print(f"Opening browser at http://localhost:{port}")

def find_available_port(start_port=8000, max_port=8100):
    """Find an available port to use"""
    for port in range(start_port, max_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
    raise RuntimeError(f"No available ports found between {start_port} and {max_port}")

def start_server(port=8000):
    """Start the HTTP server"""
    try:
        # Try to find available port
        port = find_available_port(port)
        
        # Create server
        server = socketserver.TCPServer(("", port), SonarRequestHandler)
        
        print(f"Starting server on port {port}...")
        
        # Open browser in a separate thread
        threading.Thread(target=open_browser, args=(port,), daemon=True).start()
        
        # Start server
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.server_close()
        print("Server stopped.")
    except Exception as e:
        print(f"Error starting server: {e}")

if __name__ == "__main__":
    # Start the server
    print("SonarQube Metrics Viewer")
    print("=========================")
    print("Starting local server...")
    start_server()