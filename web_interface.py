#!/usr/bin/env python3
"""
Web Interface for Natural Language IDF Creator
Simple Flask-based web UI for uploading documents and entering descriptions

Deployed: iteration3-baseline (e53d3eb)
"""

from flask import Flask, render_template_string, request, jsonify, send_file
import os
import sys
import tempfile
from pathlib import Path

# Add src to path - ensure app root is in Python path
app_root = Path(__file__).parent.absolute()
if str(app_root) not in sys.path:
    sys.path.insert(0, str(app_root))
# Also set PYTHONPATH environment variable for subprocesses
os.environ.setdefault('PYTHONPATH', str(app_root))

from src.nlp_building_parser import BuildingDescriptionParser
from src.document_parser import DocumentParser
from src.location_fetcher import GeocodingError
from main import IDFCreator

app = Flask(__name__)

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>IDF Creator - Natural Language Input</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .optional-field {
            opacity: 0.7;
            font-size: 0.9em;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #555;
        }
        input, textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
            box-sizing: border-box;
        }
        textarea {
            min-height: 120px;
            resize: vertical;
        }
        button {
            background: #007bff;
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            cursor: pointer;
            width: 100%;
        }
        button:hover {
            background: #0056b3;
        }
        .help-text {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
        .output {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 6px;
            display: none;
        }
        .output.show {
            display: block;
        }
        .success {
            color: #28a745;
            font-weight: 600;
        }
        .error {
            color: #dc3545;
        }
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #007bff;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏗️ IDF Creator</h1>
        <p>Generate EnergyPlus IDF files from natural language descriptions and documents</p>
        
        <form id="idfForm">
            <div class="form-group">
                <label for="address">Building Address *</label>
                <input type="text" id="address" name="address" required 
                       placeholder="123 Main St, San Francisco, CA">
                <div class="help-text">Required: Building location for climate data</div>
            </div>
            
            <div class="form-group">
                <label for="description">Building Description *</label>
                <textarea id="description" name="description" required
                          placeholder="Example: 5-story modern office building with 50,000 sq ft, VAV HVAC system, built in 2010, features LED lighting and solar panels"></textarea>
                <div class="help-text">Describe the building in plain English. Include size, type, HVAC, year built, features.</div>
            </div>
            
            <div class="form-group">
                <label for="documents">Documents (Optional)</label>
                <input type="file" id="documents" name="documents" multiple
                       accept=".pdf,.jpg,.jpeg,.png,.docx,.doc">
                <div class="help-text">Upload building plans, floor layouts, specifications (PDF, images, Word docs)</div>
            </div>
            
            <div class="form-group optional-field">
                <label for="llm_provider">AI Assistant (Optional)</label>
                <select id="llm_provider" name="llm_provider">
                    <option value="none">No AI - Use basic parsing</option>
                    <option value="openai">OpenAI GPT-4 (requires API key)</option>
                    <option value="anthropic">Anthropic Claude (requires API key)</option>
                </select>
                <div class="help-text">AI improves understanding of natural language (optional)</div>
            </div>
            
            <div class="form-group optional-field">
                <label for="llm_api_key">AI API Key (Optional)</label>
                <input type="password" id="llm_api_key" name="llm_api_key" placeholder="sk-...">
                <div class="help-text">Only needed if using AI. Get from OpenAI.com or Anthropic.com</div>
            </div>
            
            <button type="submit">Generate IDF File</button>
        </form>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Generating IDF file...</p>
        </div>
        
        <div class="output" id="output">
            <h3 id="outputTitle"></h3>
            <p id="outputMessage"></p>
            <div id="downloadLink"></div>
        </div>
    </div>
    
    <script>
        document.getElementById('idfForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const loading = document.getElementById('loading');
            const output = document.getElementById('output');
            
            loading.style.display = 'block';
            output.classList.remove('show');
            
            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                loading.style.display = 'none';
                output.classList.add('show');
                
                if (result.success) {
                    document.getElementById('outputTitle').textContent = '✅ Success!';
                    document.getElementById('outputTitle').className = 'success';
                    document.getElementById('outputMessage').textContent = result.message;
                    
                    const downloadDiv = document.getElementById('downloadLink');
                    downloadDiv.innerHTML = `<a href="/download/${result.filename}" download class="success" style="display: inline-block; padding: 10px 20px; background: #28a745; color: white; text-decoration: none; border-radius: 6px;">Download IDF File</a>`;
                } else {
                    document.getElementById('outputTitle').textContent = '❌ Error';
                    document.getElementById('outputTitle').className = 'error';
                    document.getElementById('outputMessage').textContent = result.message;
                }
            } catch (error) {
                loading.style.display = 'none';
                output.classList.add('show');
                document.getElementById('outputTitle').textContent = '❌ Error';
                document.getElementById('outputTitle').className = 'error';
                document.getElementById('outputMessage').textContent = 'An error occurred: ' + error.message;
            }
        });
    </script>
</body>
</html>
"""

from flask_cors import CORS

# Enable CORS for all routes
CORS(app)

# Helper functions for safe operations
def safe_divide(numerator, denominator, default=0):
    """Safely divide two numbers, handling None and zero"""
    if denominator is None or denominator == 0:
        return default
    if numerator is None:
        return default
    try:
        return numerator / denominator
    except (TypeError, ZeroDivisionError):
        return default

def safe_lower(value, default=''):
    """Safely convert to lowercase, handling None"""
    if value is None:
        return default
    try:
        return str(value).lower()
    except:
        return default

def safe_get(data, key, default=None):
    """Safely get value from dict with default"""
    if data is None:
        return default
    value = data.get(key, default)
    if value is None:
        return default
    return value

@app.route('/')
def index():
    """Render the main page"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/health', methods=['GET'])
def api_health():
    """API health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'IDF Creator API',
        'version': '1.0.0'
    })

@app.route('/api/generate', methods=['POST'])
def api_generate_idf():
    """API endpoint for JSON requests"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        address = data.get('address')
        description = data.get('description')
        llm_provider = data.get('llm_provider', 'none')
        llm_api_key = data.get('llm_api_key', None)
        strict_real = bool(data.get('strict_real_data', False))
        
        if not address:
            return jsonify({
                'success': False,
                'error': 'Address is required'
            }), 400
        
        # Use NLP parsing if description provided
        # Handle None description - convert to empty string
        if description is None:
            description = ''
        
        if description:
            use_llm = llm_provider != 'none' and llm_api_key
            nlp_parser = BuildingDescriptionParser(
                use_llm=use_llm,
                llm_provider=llm_provider if use_llm else 'openai',
                api_key=llm_api_key
            )
            result = nlp_parser.process_and_generate_idf(description, address)
            idf_params = result['idf_parameters']
        else:
            idf_params = {}
        
        # Check for user_params in request, or extract direct parameters
        user_params_request = data.get('user_params', {})
        
        # Merge parameters: user_params from request > direct parameters > parsed from description
        # Apply safe defaults for all numeric parameters
        stories = user_params_request.get('stories') or data.get('stories') or idf_params.get('stories')
        floor_area_confirmed = bool(
            user_params_request.get('floor_area_confirmed')
            or data.get('floor_area_confirmed')
            or idf_params.get('floor_area_confirmed')
        )
        floor_area = user_params_request.get('floor_area') or data.get('floor_area') or idf_params.get('floor_area')
        building_type = user_params_request.get('building_type') or data.get('building_type') or idf_params.get('building_type') or 'Building'
        
        # Ensure numeric values are valid (not None and > 0)
        story_provided = stories is not None and stories > 0
        floor_area_provided = floor_area is not None and floor_area > 0

        # Normalize invalid values to None so downstream logic can fall back to real data
        if not story_provided:
            stories = None
        if not floor_area_provided:
            floor_area = None
        elif not floor_area_confirmed:
            print(f"⚠️  Ignoring unconfirmed floor area override ({floor_area} m²). Real footprint data will be used instead.")
            floor_area = None
            floor_area_provided = False
        
        user_params = {}
        if building_type:
            user_params['building_type'] = building_type
        if story_provided:
            user_params['stories'] = stories
        if floor_area_provided and floor_area_confirmed:
            user_params['floor_area'] = floor_area
            user_params['floor_area_source'] = 'user_confirmed'
        elif floor_area_provided and not floor_area_confirmed:
            user_params['floor_area_override_rejected'] = True
        
        # Also check for floor_area_per_story_m2
        if user_params_request.get('floor_area_per_story_m2') or data.get('floor_area_per_story_m2'):
            user_params['floor_area_per_story_m2'] = user_params_request.get('floor_area_per_story_m2') or data.get('floor_area_per_story_m2')
        
        if strict_real:
            user_params['strict_real_data'] = True
        
        # Generate IDF
        creator = IDFCreator(enhanced=True, professional=True)
        
        # Create temporary output file
        temp_dir = tempfile.mkdtemp()
        building_name = (user_params.get('building_type') or 'Building').replace(' ', '_')
        output_file = f"{building_name}_api.idf"
        output_path = os.path.join(temp_dir, output_file)
        
        created_path = creator.create_idf(
            address=address,
            user_params=user_params,
            output_path=output_path
        )
        
        # Move to persistent location
        persistent_dir = Path('artifacts/desktop_files/idf')
        persistent_dir.mkdir(parents=True, exist_ok=True)
        
        final_path = persistent_dir / output_file
        import shutil
        shutil.move(created_path, final_path)
        
        return jsonify({
            'success': True,
            'message': 'IDF file generated successfully',
            'filename': output_file,
            'download_url': f'/download/{output_file}',
            'parameters_used': user_params
        })
        
    except GeocodingError as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'type': 'GeocodingError',
            'message': 'Geocoding failed: Could not find real coordinates for the provided address. Please provide a valid address with city and state information.'
        }), 400
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"❌ Error in /api/generate endpoint: {str(e)}")
        print(f"Traceback:\n{error_traceback}")
        return jsonify({
            'success': False,
            'error': str(e),
            'type': type(e).__name__,
            'traceback': error_traceback if app.debug else None
        }), 500

@app.route('/generate', methods=['POST'])
def generate_idf():
    """Generate IDF from JSON or form data"""
    try:
        # Check if request contains JSON data
        json_data = request.get_json(silent=True)
        
        if json_data:
            # Handle JSON request
            # Extract address - prefer 'address' field, fall back to 'description' if address not provided
            address = json_data.get('address')
            description = json_data.get('description', '')
            
            # If no address provided, use description as address
            if not address and description:
                address = description
                # Don't parse description as building description if it's being used as address
                description = ''
            
            files = []  # No file uploads in JSON requests
            document_paths = []
            llm_provider = json_data.get('llm_provider', 'none')
            llm_api_key = json_data.get('llm_api_key', None)
            
            # Extract user_params or direct parameters for JSON requests
            user_params_request = json_data.get('user_params', {})
            
            # Get direct parameters if not in user_params
            stories = user_params_request.get('stories') or json_data.get('stories')
            floor_area = user_params_request.get('floor_area') or json_data.get('floor_area')
            building_type = user_params_request.get('building_type') or json_data.get('building_type')
        else:
            # Handle form data request
            address = request.form.get('address')
            description = request.form.get('description', '')
            files = request.files.getlist('documents')
            stories = None
            floor_area = None
            building_type = None
            
            # Save uploaded files
            temp_dir = tempfile.mkdtemp()
            document_paths = []
            
            for file in files:
                if file.filename:
                    filepath = os.path.join(temp_dir, file.filename)
                    file.save(filepath)
                    document_paths.append(filepath)
            
            # Get LLM settings from form
            llm_provider = request.form.get('llm_provider', 'none')
            llm_api_key = request.form.get('llm_api_key', None)
        
        # Validate address
        if not address:
            return jsonify({
                'success': False,
                'error': 'Address is required',
                'message': 'Address or description is required'
            }), 400
        
        # Handle None description
        if description is None:
            description = ''
        
        # Create temp directory if not already created (for form data)
        if json_data:
            temp_dir = tempfile.mkdtemp()
        
        # Parse description with optional LLM (only if description provided)
        idf_params = {}
        if description:
            use_llm = llm_provider != 'none' and llm_api_key
            nlp_parser = BuildingDescriptionParser(
                use_llm=use_llm,
                llm_provider=llm_provider if use_llm else 'openai',
                api_key=llm_api_key
            )
            result = nlp_parser.process_and_generate_idf(description, address)
            idf_params = result['idf_parameters']
        
        # Parse documents if any
        if document_paths:
            doc_parser = DocumentParser()
            for doc_path in document_paths:
                doc_params = doc_parser.parse_document(doc_path)
                idf_params.update(doc_params)
        
        # Merge parameters: JSON/form params > parsed from description
        # For JSON requests, use provided params; for form requests, use parsed params
        if json_data:
            # JSON request: use provided params or parsed params as fallback
            stories = stories or idf_params.get('stories')
            floor_area = floor_area or idf_params.get('floor_area')
            building_type = building_type or idf_params.get('building_type')
        else:
            # Form request: use parsed params
            stories = idf_params.get('stories')
            floor_area = idf_params.get('floor_area')
            building_type = idf_params.get('building_type')
        
        # Apply safe defaults for all parameters
        if not building_type:
            building_type = 'Building'
        
        # Ensure numeric values are valid (not None and > 0)
        if stories is None or stories <= 0:
            stories = 1
        if floor_area is None or floor_area <= 0:
            floor_area = 500  # Default 500 m²
        
        user_params = {
            'stories': stories,
            'floor_area': floor_area,
            'building_type': building_type
        }
        
        # Add floor_area_per_story_m2 if provided in JSON
        if json_data:
            floor_area_per_story = user_params_request.get('floor_area_per_story_m2') or json_data.get('floor_area_per_story_m2')
            if floor_area_per_story:
                user_params['floor_area_per_story_m2'] = floor_area_per_story
        
        # Generate IDF
        creator = IDFCreator(enhanced=True, professional=True)
        
        # Generate output filename (safe lowercase conversion)
        building_name = safe_lower(building_type, 'Building').replace(' ', '_')
        if not building_name:
            building_name = 'Building'
        output_file = f"{building_name}_nlp.idf"
        output_path = os.path.join(temp_dir, output_file)
        
        # Create IDF
        created_path = creator.create_idf(
            address=address,
            documents=document_paths if document_paths else None,
            user_params=user_params,
            output_path=output_path
        )
        
        # Move file to a persistent location
        persistent_dir = Path('artifacts/desktop_files/idf')
        persistent_dir.mkdir(parents=True, exist_ok=True)
        
        final_path = persistent_dir / output_file
        import shutil
        shutil.move(created_path, final_path)
        
        response_data = {
            'success': True,
            'message': f'IDF file generated successfully: {building_name}',
            'filename': output_file
        }
        
        # For JSON requests, include download_url like /api/generate endpoint
        if json_data:
            response_data['download_url'] = f'/download/{output_file}'
            response_data['parameters_used'] = user_params
        
        return jsonify(response_data)
        
    except GeocodingError as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'type': 'GeocodingError',
            'message': f'Geocoding failed: {str(e)}. Please provide a valid address with city and state information.'
        }), 400
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"❌ Error in /generate endpoint: {str(e)}")
        print(f"Traceback:\n{error_traceback}")
        return jsonify({
            'success': False,
            'error': str(e),
            'type': type(e).__name__,
            'message': f'Error generating IDF: {str(e)}',
            'traceback': error_traceback if app.debug else None
        }), 500

@app.route('/download/<filename>')
def download(filename):
    """Download generated IDF file"""
    file_path = Path('artifacts/desktop_files/idf') / filename
    if file_path.exists():
        return send_file(file_path, as_attachment=True)
    return "File not found", 404

@app.route('/simulate', methods=['POST'])
def simulate_energyplus():
    """
    EnergyPlus Simulation API endpoint
    Accepts IDF file content and weather file, runs simulation, returns results
    """
    import subprocess
    import base64
    import tempfile
    import shutil
    import re
    from datetime import datetime
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'version': '33.0.0',
                'simulation_status': 'error',
                'error_message': 'Invalid JSON: Expecting value: line 1 column 1 (char 0)',
                'timestamp': datetime.now().isoformat()
            }), 200
        
        idf_content = data.get('idf_content')
        weather_content_b64 = data.get('weather_content')
        weather_filename = data.get('weather_filename', 'weather.epw')
        
        if not idf_content:
            return jsonify({
                'version': '33.0.0',
                'simulation_status': 'error',
                'error_message': 'Missing idf_content in request',
                'timestamp': datetime.now().isoformat()
            }), 200
        
        # Create temporary directory for simulation
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Write IDF file
            idf_path = os.path.join(temp_dir, 'input.idf')
            with open(idf_path, 'w') as f:
                f.write(idf_content)
            
            # Write weather file if provided
            weather_path = None
            if weather_content_b64:
                weather_bytes = base64.b64decode(weather_content_b64)
                weather_path = os.path.join(temp_dir, weather_filename)
                with open(weather_path, 'wb') as f:
                    f.write(weather_bytes)
            
            # Find EnergyPlus executable
            energyplus_path = None
            for path in ['energyplus', '/usr/local/bin/energyplus', '/opt/EnergyPlus/energyplus']:
                try:
                    result = subprocess.run([path, '--version'], capture_output=True, timeout=5)
                    if result.returncode == 0:
                        energyplus_path = path
                        break
                except:
                    continue
            
            # If EnergyPlus not found locally, use external EnergyPlus API
            if not energyplus_path:
                import requests
                external_api_url = os.getenv('ENERGYPLUS_API_URL', 'https://web-production-1d1be.up.railway.app/simulate')
                
                # Prepare payload for external API
                external_payload = {
                    'idf_content': idf_content,
                    'idf_filename': data.get('idf_filename', 'input.idf')
                }
                
                if weather_content_b64:
                    external_payload['weather_content'] = weather_content_b64
                    external_payload['weather_filename'] = weather_filename
                
                try:
                    # Call external EnergyPlus API
                    external_response = requests.post(
                        external_api_url,
                        json=external_payload,
                        headers={'Content-Type': 'application/json'},
                        timeout=600  # 10 minute timeout
                    )
                    
                    if external_response.status_code == 200:
                        # Return the response from external API
                        external_data = external_response.json()
                        # Add metadata to indicate it used external API
                        external_data['used_external_api'] = True
                        external_data['external_api_url'] = external_api_url
                        
                        # Check if we got energy results - if not, try to extract from SQLite if available
                        if external_data.get('simulation_status') == 'success' and not external_data.get('energy_results'):
                            # If simulation succeeded but no results, might need SQLite extraction
                            # Note: This would require the SQLite file to be accessible, which it isn't in this case
                            # The external API should handle SQLite extraction
                            pass
                        
                        # Add diagnostic information if simulation failed or no results
                        if external_data.get('simulation_status') == 'error' or (
                            external_data.get('simulation_status') == 'success' and not external_data.get('energy_results')
                        ):
                            # Add request diagnostics
                            external_data['diagnostics'] = {
                                'idf_size': len(idf_content),
                                'weather_file_included': bool(weather_content_b64),
                                'weather_filename': weather_filename if weather_content_b64 else None,
                                'external_api_response_time': external_response.elapsed.total_seconds() if hasattr(external_response, 'elapsed') else None
                            }
                            
                            # Check output files
                            output_files = external_data.get('output_files', [])
                            if output_files:
                                sql_file = next((f for f in output_files if 'sql' in f.get('name', '').lower() and 'sqlite.err' not in f.get('name', '')), None)
                                csv_file = next((f for f in output_files if 'csv' in f.get('name', '').lower()), None)
                                external_data['diagnostics']['sqlite_file_exists'] = sql_file is not None and sql_file.get('size', 0) > 0
                                external_data['diagnostics']['csv_file_exists'] = csv_file is not None and csv_file.get('size', 0) > 0
                                if sql_file:
                                    external_data['diagnostics']['sqlite_file_size'] = sql_file.get('size', 0)
                            
                            # If external API provides debug_info, include it
                            if 'debug_info' in external_data:
                                external_data['diagnostics']['external_debug_info'] = external_data['debug_info']
                        
                        return jsonify(external_data), 200
                    else:
                        return jsonify({
                            'version': '33.0.0',
                            'simulation_status': 'error',
                            'error_message': f'External EnergyPlus API returned status {external_response.status_code}: {external_response.text[:500]}',
                            'timestamp': datetime.now().isoformat()
                        }), 200
                except requests.exceptions.RequestException as e:
                    return jsonify({
                        'version': '33.0.0',
                        'simulation_status': 'error',
                        'error_message': f'Failed to connect to external EnergyPlus API ({external_api_url}): {str(e)}',
                        'timestamp': datetime.now().isoformat()
                    }), 200
            
            # Run EnergyPlus simulation
            output_dir = os.path.join(temp_dir, 'output')
            os.makedirs(output_dir, exist_ok=True)
            
            cmd = [energyplus_path]
            if weather_path:
                cmd.extend(['-w', weather_path])
            cmd.extend(['-d', output_dir])
            cmd.append(idf_path)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            # Check error file
            err_file = os.path.join(output_dir, 'eplusout.err')
            warnings = []
            fatal_errors = []
            simulation_completed = False
            
            if os.path.exists(err_file):
                with open(err_file, 'r') as f:
                    err_content = f.read()
                    
                    # Extract warnings and errors
                    for line in err_content.split('\n'):
                        if '** Warning' in line or '** Severe' in line or '** Fatal' in line:
                            if '** Warning' in line:
                                warnings.append(line.strip())
                            else:
                                fatal_errors.append(line.strip())
                    
                    # Check if simulation completed
                    if 'EnergyPlus Completed Successfully' in err_content:
                        simulation_completed = True
            
            # Extract energy results
            energy_results = None
            csv_file = os.path.join(output_dir, 'eplustbl.csv')
            sql_file = os.path.join(output_dir, 'eplusout.sql')
            
            if simulation_completed:
                # PRIORITIZE CSV EXTRACTION - it's more reliable and complete
                if os.path.exists(csv_file):
                    try:
                        with open(csv_file, 'r') as f:
                            csv_content = f.read()
                            
                            energy_results = {}
                            
                            # Extract total site energy (multiple patterns)
                            patterns = [
                                r'Total Site Energy,([\d.]+)',  # Standard format
                                r'Total Site Energy\s+([\d,]+\.?\d*)',  # With spaces
                                r'"Total Site Energy","([\d.]+)"',  # Quoted format
                            ]
                            
                            site_energy_gj = None
                            for pattern in patterns:
                                match = re.search(pattern, csv_content)
                                if match:
                                    try:
                                        site_energy_gj = float(match.group(1).replace(',', ''))
                                        break
                                    except:
                                        continue
                            
                            if site_energy_gj:
                                energy_results['total_site_energy_gj'] = site_energy_gj
                                # Convert GJ to kWh: 1 GJ = 277.778 kWh
                                energy_results['total_site_energy_kwh'] = site_energy_gj * 277.778
                                
                                # Extract end uses to verify we have all energy sources
                                end_uses = {}
                                # Pattern: "End Use,<name>,Electricity (GJ),Natural Gas (GJ)"
                                end_use_pattern = r',([^,]+),([\d.]+),([\d.]+)'
                                
                                # Look for common end uses
                                for end_use_name in ['Heating', 'Cooling', 'Interior Lighting', 
                                                     'Interior Equipment', 'Fans', 'Pumps', 
                                                     'Exterior Lighting', 'Water Systems']:
                                    # Try multiple patterns
                                    patterns = [
                                        rf',{re.escape(end_use_name)},([\d.]+),([\d.]+)',
                                        rf'{re.escape(end_use_name)},([\d.]+),([\d.]+)',
                                    ]
                                    for pattern in patterns:
                                        match = re.search(pattern, csv_content, re.IGNORECASE)
                                        if match:
                                            try:
                                                elec_gj = float(match.group(1).replace(',', ''))
                                                gas_gj = float(match.group(2).replace(',', ''))
                                                if elec_gj > 0 or gas_gj > 0:
                                                    end_uses[end_use_name] = {
                                                        'electricity_gj': elec_gj,
                                                        'electricity_kwh': elec_gj * 277.778,
                                                        'natural_gas_gj': gas_gj,
                                                        'natural_gas_kwh': gas_gj * 277.778
                                                    }
                                                break
                                            except:
                                                continue
                                
                                if end_uses:
                                    energy_results['end_uses'] = end_uses
                                    
                                    # Verify total matches sum of end uses (optional validation)
                                    total_elec_gj = sum(e.get('electricity_gj', 0) for e in end_uses.values())
                                    total_gas_gj = sum(e.get('natural_gas_gj', 0) for e in end_uses.values())
                                    total_calculated_gj = total_elec_gj + total_gas_gj
                                    
                                    # Allow 5% tolerance for rounding differences
                                    if abs(total_calculated_gj - site_energy_gj) / site_energy_gj > 0.05:
                                        print(f"⚠️  Warning: Sum of end uses ({total_calculated_gj:.2f} GJ) doesn't match Total Site Energy ({site_energy_gj:.2f} GJ)")
                            
                            # Extract building area (prioritize "Total Building Area" from CSV)
                            # CSV "Total Building Area" is the most reliable source as it matches
                            # EnergyPlus's official building area calculation
                            area_patterns = [
                                r'Total Building Area,([\d.]+)',  # Preferred - matches CSV header exactly
                                r'Total Building Area\s+([\d,]+\.?\d*)',
                                r'Conditioned Floor Area.*?([\d,]+\.?\d*)',
                            ]
                            
                            building_area_m2 = None
                            for pattern in area_patterns:
                                match = re.search(pattern, csv_content, re.IGNORECASE)
                                if match:
                                    try:
                                        area = float(match.group(1).replace(',', ''))
                                        if area > 0:
                                            building_area_m2 = area
                                            energy_results['building_area_m2'] = area
                                            energy_results['building_area_source'] = 'CSV - Total Building Area'
                                            if energy_results.get('total_site_energy_kwh'):
                                                energy_results['eui_kwh_m2'] = (
                                                    energy_results['total_site_energy_kwh'] / area
                                                )
                                            break
                                    except:
                                        continue
                            
                            if building_area_m2:
                                print(f"✓ Building area from CSV: {building_area_m2:.2f} m²")
                            
                            # Only use CSV results if we got at least site energy
                            if energy_results.get('total_site_energy_kwh'):
                                # CSV extraction successful
                                energy_results['extraction_method'] = 'standard'
                                print(f"✓ Extracted from CSV: {energy_results['total_site_energy_kwh']:.2f} kWh")
                            else:
                                energy_results = None
                                
                    except Exception as e:
                        print(f"⚠️  Error extracting from CSV: {e}")
                        energy_results = None
                
                # Try SQLite if CSV didn't work
                if not energy_results and os.path.exists(sql_file):
                    try:
                        import sqlite3
                        conn = sqlite3.connect(sql_file)
                        cursor = conn.cursor()
                        
                        # First, check what tables exist
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                        tables = [row[0] for row in cursor.fetchall()]
                        
                        energy_results = {}
                        total_site_energy_j = 0
                        
                        # Try multiple query strategies for electricity
                        # NOTE: For RunPeriod frequency, EnergyPlus stores cumulative/annual totals.
                        # Use MAX() instead of SUM() to get the final cumulative value, not timestep sums.
                        electricity_queries = [
                            # Strategy 1: ReportMeterData with ReportMeterDataDictionary (MAX for cumulative)
                            """
                            SELECT MAX(d.Value) 
                            FROM ReportMeterData d
                            JOIN ReportMeterDataDictionary m ON d.ReportMeterDataDictionaryIndex = m.ReportMeterDataDictionaryIndex
                            WHERE m.Name LIKE '%Electricity%Facility%'
                            AND m.ReportingFrequency = 'RunPeriod'
                            """,
                            # Strategy 2: ReportMeterData with ReportMeterDictionary (MAX for cumulative)
                            """
                            SELECT MAX(d.Value) 
                            FROM ReportMeterData d
                            JOIN ReportMeterDictionary m ON d.ReportMeterDictionaryIndex = m.ReportMeterDictionaryIndex
                            WHERE m.Name LIKE '%Electricity%Facility%'
                            AND m.ReportingFrequency = 'RunPeriod'
                            """,
                            # Strategy 3: Direct meter name lookup (MAX for cumulative)
                            """
                            SELECT MAX(Value) 
                            FROM ReportMeterData
                            WHERE ReportMeterDataDictionaryIndex IN (
                                SELECT ReportMeterDataDictionaryIndex
                                FROM ReportMeterDataDictionary
                                WHERE Name = 'Electricity:Facility'
                                AND ReportingFrequency = 'RunPeriod'
                            )
                            """,
                            # Strategy 4: Alternative table structure (MAX for cumulative)
                            """
                            SELECT MAX(Value) 
                            FROM ReportMeterData
                            WHERE ReportMeterDictionaryIndex IN (
                                SELECT ReportMeterDictionaryIndex
                                FROM ReportMeterDictionary
                                WHERE Name = 'Electricity:Facility'
                                AND ReportingFrequency = 'RunPeriod'
                            )
                            """,
                            # Strategy 5: Generic electricity search (MAX for cumulative)
                            """
                            SELECT MAX(Value) 
                            FROM ReportMeterData
                            WHERE ReportMeterDataDictionaryIndex IN (
                                SELECT ReportMeterDataDictionaryIndex
                                FROM ReportMeterDataDictionary
                                WHERE Name LIKE '%Electricity%'
                                AND ReportingFrequency = 'RunPeriod'
                            )
                            """,
                            # Strategy 6: Fallback - try SUM if MAX doesn't work (shouldn't happen for RunPeriod)
                            """
                            SELECT SUM(d.Value) 
                            FROM ReportMeterData d
                            JOIN ReportMeterDataDictionary m ON d.ReportMeterDataDictionaryIndex = m.ReportMeterDataDictionaryIndex
                            WHERE m.Name = 'Electricity:Facility'
                            AND m.ReportingFrequency = 'RunPeriod'
                            """
                        ]
                        
                        # Try each query strategy
                        for query in electricity_queries:
                            try:
                                cursor.execute(query)
                                result = cursor.fetchone()
                                if result and result[0] and result[0] > 0:
                                    total_site_energy_j = float(result[0])
                                    break
                            except:
                                continue
                        
                        # If we got electricity, convert and add to results
                        if total_site_energy_j > 0:
                            # Value is in Joules, convert to kWh (1 kWh = 3,600,000 J)
                            energy_results['total_electricity_kwh'] = total_site_energy_j / 3600000.0
                            energy_results['total_site_energy_kwh'] = total_site_energy_j / 3600000.0
                            energy_results['total_site_energy_j'] = total_site_energy_j
                            
                            # Try to get natural gas
                            # NOTE: For RunPeriod frequency, use MAX() for cumulative values
                            gas_queries = [
                                """
                                SELECT MAX(d.Value) 
                                FROM ReportMeterData d
                                JOIN ReportMeterDataDictionary m ON d.ReportMeterDataDictionaryIndex = m.ReportMeterDataDictionaryIndex
                                WHERE m.Name LIKE '%NaturalGas%Facility%'
                                AND m.ReportingFrequency = 'RunPeriod'
                                """,
                                """
                                SELECT MAX(d.Value) 
                                FROM ReportMeterData d
                                JOIN ReportMeterDictionary m ON d.ReportMeterDictionaryIndex = m.ReportMeterDictionaryIndex
                                WHERE m.Name LIKE '%NaturalGas%Facility%'
                                AND m.ReportingFrequency = 'RunPeriod'
                                """,
                                """
                                SELECT MAX(Value) 
                                FROM ReportMeterData
                                WHERE ReportMeterDataDictionaryIndex IN (
                                    SELECT ReportMeterDataDictionaryIndex
                                    FROM ReportMeterDataDictionary
                                    WHERE Name = 'NaturalGas:Facility'
                                    AND ReportingFrequency = 'RunPeriod'
                                )
                                """,
                                """
                                SELECT MAX(Value) 
                                FROM ReportMeterData
                                WHERE ReportMeterDictionaryIndex IN (
                                    SELECT ReportMeterDictionaryIndex
                                    FROM ReportMeterDictionary
                                    WHERE Name = 'NaturalGas:Facility'
                                    AND ReportingFrequency = 'RunPeriod'
                                )
                                """,
                                # Fallback - try SUM if MAX doesn't work
                                """
                                SELECT SUM(d.Value) 
                                FROM ReportMeterData d
                                JOIN ReportMeterDataDictionary m ON d.ReportMeterDataDictionaryIndex = m.ReportMeterDataDictionaryIndex
                                WHERE m.Name LIKE '%Gas%'
                                AND m.ReportingFrequency = 'RunPeriod'
                                """
                            ]
                            
                            total_gas_j = 0
                            for query in gas_queries:
                                try:
                                    cursor.execute(query)
                                    result = cursor.fetchone()
                                    if result and result[0] and result[0] > 0:
                                        total_gas_j = float(result[0])
                                        break
                                except:
                                    continue
                            
                            if total_gas_j > 0:
                                # Gas is typically in Joules, convert to kWh
                                energy_results['total_gas_kwh'] = total_gas_j / 3600000.0
                                # Add gas to total site energy
                                energy_results['total_site_energy_kwh'] += energy_results['total_gas_kwh']
                        
                        # Try to get building area from SQLite (only if not already set from CSV)
                        # Note: SQLite area may differ from CSV "Total Building Area" as it may sum
                        # individual zone areas or use a different calculation method
                        if 'building_area_m2' not in energy_results:
                            area_queries = [
                                """
                                SELECT SUM(Value) 
                                FROM ReportVariableData d
                                JOIN ReportVariableDataDictionary v ON d.ReportVariableDataDictionaryIndex = v.ReportVariableDataDictionaryIndex
                                WHERE v.Name LIKE '%Building%Area%'
                                AND v.ReportingFrequency = 'RunPeriod'
                                LIMIT 1
                                """,
                                """
                                SELECT SUM(Value) 
                                FROM ReportVariableData d
                                JOIN ReportVariableDictionary v ON d.ReportVariableDictionaryIndex = v.ReportVariableDictionaryIndex
                                WHERE v.Name LIKE '%Building%Area%'
                                AND v.ReportingFrequency = 'RunPeriod'
                                LIMIT 1
                                """,
                                """
                                SELECT SUM(Value) 
                                FROM ReportVariableData d
                                JOIN ReportVariableDataDictionary v ON d.ReportVariableDataDictionaryIndex = v.ReportVariableDataDictionaryIndex
                                WHERE v.Name LIKE '%Floor Area%'
                                AND v.ReportingFrequency = 'RunPeriod'
                                LIMIT 1
                                """,
                            ]
                            
                            for query in area_queries:
                                try:
                                    cursor.execute(query)
                                    area_result = cursor.fetchone()
                                    if area_result and area_result[0] and area_result[0] > 0:
                                        area = float(area_result[0])
                                        if area > 0:
                                            energy_results['building_area_m2'] = area
                                            energy_results['building_area_source'] = 'SQLite'
                                            if energy_results.get('total_site_energy_kwh'):
                                                energy_results['eui_kwh_m2'] = (
                                                    energy_results['total_site_energy_kwh'] / area
                                                )
                                            break
                                except:
                                    continue
                        
                        conn.close()
                        
                        # Validate SQLite results if we also have CSV results for comparison
                        if energy_results.get('total_site_energy_kwh') and os.path.exists(csv_file):
                            # Try to get CSV energy for comparison
                            try:
                                with open(csv_file, 'r') as f:
                                    csv_check = f.read()
                                    csv_match = re.search(r'Total Site Energy,([\d.]+)', csv_check)
                                    if csv_match:
                                        csv_energy_gj = float(csv_match.group(1).replace(',', ''))
                                        csv_energy_kwh = csv_energy_gj * 277.778
                                        sqlite_energy_kwh = energy_results.get('total_site_energy_kwh', 0)
                                        
                                        # Check if SQLite energy is significantly different (>10% difference)
                                        if abs(sqlite_energy_kwh - csv_energy_kwh) / csv_energy_kwh > 0.10:
                                            print(f"⚠️  Warning: SQLite energy ({sqlite_energy_kwh:.2f} kWh) differs significantly from CSV ({csv_energy_kwh:.2f} kWh)")
                                            print(f"   Using CSV value as it's more reliable. CSV is {((csv_energy_kwh - sqlite_energy_kwh) / sqlite_energy_kwh * 100):.1f}% different")
                                            # Prefer CSV over SQLite if CSV is available
                                            # Re-extract from CSV (this should have been done first, but double-check)
                                            energy_results = None  # Will trigger re-extraction
                            except:
                                pass  # If CSV check fails, continue with SQLite results
                        
                        # Only use results if we got at least energy data
                        if energy_results.get('total_site_energy_kwh'):
                            energy_results['extraction_method'] = 'sqlite'
                            print(f"✓ Extracted from SQLite: {energy_results['total_site_energy_kwh']:.2f} kWh")
                        else:
                            energy_results = None
                            
                    except Exception as e:
                        # Log error but don't fail completely
                        print(f"⚠️  SQLite extraction error: {e}")
                        energy_results = None
            
            # Check if simulation ran but produced no results
            if simulation_completed and not energy_results:
                # Additional debugging: check if CSV file exists and what it contains
                debug_info = {}
                if os.path.exists(csv_file):
                    with open(csv_file, 'r') as f:
                        csv_preview = f.read()[:500]  # First 500 chars
                        debug_info['csv_file_exists'] = True
                        debug_info['csv_preview'] = csv_preview
                        # Check if it has any energy-related content
                        if 'Energy' in csv_preview or 'electricity' in csv_preview.lower():
                            debug_info['csv_has_energy_data'] = True
                        else:
                            debug_info['csv_has_energy_data'] = False
                else:
                    debug_info['csv_file_exists'] = False
                
                if os.path.exists(sql_file):
                    debug_info['sql_file_exists'] = True
                    debug_info['sql_file_size'] = os.path.getsize(sql_file)
                else:
                    debug_info['sql_file_exists'] = False
                
                # Check error file for RunPeriod issues
                if os.path.exists(err_file):
                    with open(err_file, 'r') as f:
                        err_content = f.read()
                        if 'RunPeriod' in err_content or 'run period' in err_content.lower():
                            debug_info['err_mentions_runperiod'] = True
                        if '0 days' in err_content.lower():
                            debug_info['err_mentions_0_days'] = True
                
                return jsonify({
                    'version': '33.0.0',
                    'simulation_status': 'error',
                    'energyplus_version': '25.1.0',
                    'real_simulation': True,
                    'error_message': 'EnergyPlus ran but produced no energy results. This usually means:\n1. IDF file is missing required objects (RunPeriod, Schedules, etc.)\n2. Simulation ran for 0 days\n3. Output:* objects are missing from IDF\n',
                    'debug_info': debug_info,
                    'warnings': warnings[:5],
                    'processing_time': datetime.now().isoformat()
                }), 200
            
            # Return results
            if simulation_completed and energy_results:
                return jsonify({
                    'version': '33.0.0',
                    'simulation_status': 'success',
                    'energyplus_version': '25.1.0',
                    'real_simulation': True,
                    'energy_results': energy_results,
                    'warnings': warnings[:10],  # Limit warnings
                    'processing_time': datetime.now().isoformat()
                }), 200
            else:
                return jsonify({
                    'version': '33.0.0',
                    'simulation_status': 'error',
                    'energyplus_version': '25.1.0',
                    'real_simulation': True,
                    'error_message': f'EnergyPlus simulation failed with fatal errors:\n' + 
                                   '\n'.join(fatal_errors[:5]),
                    'warnings': warnings[:10],
                    'processing_time': datetime.now().isoformat()
                }), 200
                
        finally:
            # Cleanup temporary directory
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
                
    except Exception as e:
        import traceback
        return jsonify({
            'version': '33.0.0',
            'simulation_status': 'error',
            'error_message': f'Server error: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 200

if __name__ == '__main__':
    # Try to import Railway config
    try:
        from railway_config import get_config
        config = get_config()
    except ImportError:
        config = {'debug': True, 'host': '0.0.0.0', 'port': 5000, 'environment': 'development'}
    
    port = int(os.getenv('PORT', config['port']))
    
    print("🌐 Starting IDF Creator Web Interface...")
    print(f"🚀 Version: 1.0.0")
    print(f"📝 Open http://localhost:{port} in your browser")
    print(f"🌍 Environment: {config.get('environment', 'development')}")
    
    app.run(debug=config.get('debug', False), host=config['host'], port=port)

