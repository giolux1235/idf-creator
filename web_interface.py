#!/usr/bin/env python3
"""
Web Interface for Natural Language IDF Creator
Simple Flask-based web UI for uploading documents and entering descriptions
"""

from flask import Flask, render_template_string, request, jsonify, send_file
import os
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.nlp_building_parser import BuildingDescriptionParser
from src.document_parser import DocumentParser
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
        
        # Generate IDF
        creator = IDFCreator(enhanced=True, professional=True)
        
        user_params = {
            'stories': idf_params.get('stories'),
            'floor_area': idf_params.get('floor_area'),
            'building_type': idf_params.get('building_type') or 'Building'
        }
        if strict_real:
            user_params['strict_real_data'] = True
        
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
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'type': type(e).__name__
        }), 500

@app.route('/generate', methods=['POST'])
def generate_idf():
    """Generate IDF from form data"""
    try:
        address = request.form.get('address')
        description = request.form.get('description')
        files = request.files.getlist('documents')
        
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
        
        # Parse description with optional LLM
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
        
        # Generate IDF
        creator = IDFCreator(enhanced=True, professional=True)
        
        user_params = {
            'stories': idf_params.get('stories'),
            'floor_area': idf_params.get('floor_area'),
            'building_type': idf_params.get('building_type') or 'Building'
        }
        
        # Generate output filename
        building_name = (idf_params.get('building_type') or 'Building').replace(' ', '_')
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
        
        return jsonify({
            'success': True,
            'message': f'IDF file generated successfully: {building_name}',
            'filename': output_file
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error generating IDF: {str(e)}'
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
            
            if not energyplus_path:
                return jsonify({
                    'version': '33.0.0',
                    'simulation_status': 'error',
                    'error_message': 'EnergyPlus executable not found',
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
                # Try to extract from CSV
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
                                energy_results['total_site_energy_kwh'] = site_energy_gj * 277.778
                            
                            # Extract building area
                            area_patterns = [
                                r'Total Building Area,([\d.]+)',
                                r'Total Building Area\s+([\d,]+\.?\d*)',
                                r'Conditioned Floor Area.*?([\d,]+\.?\d*)',
                            ]
                            
                            for pattern in area_patterns:
                                match = re.search(pattern, csv_content, re.IGNORECASE)
                                if match:
                                    try:
                                        area = float(match.group(1).replace(',', ''))
                                        if area > 0:
                                            energy_results['building_area_m2'] = area
                                            if energy_results.get('total_site_energy_kwh'):
                                                energy_results['eui_kwh_m2'] = (
                                                    energy_results['total_site_energy_kwh'] / area
                                                )
                                            break
                                    except:
                                        continue
                            
                            # If we got any results, use them
                            if energy_results:
                                pass  # energy_results already set
                            else:
                                energy_results = None
                                
                    except Exception as e:
                        energy_results = None
                
                # Try SQLite if CSV didn't work
                if not energy_results and os.path.exists(sql_file):
                    try:
                        import sqlite3
                        conn = sqlite3.connect(sql_file)
                        cursor = conn.cursor()
                        
                        # Query for electricity meter (value is in Joules)
                        cursor.execute("""
                            SELECT SUM(d.Value) 
                            FROM ReportMeterData d
                            JOIN ReportMeterDataDictionary m ON d.ReportMeterDataDictionaryIndex = m.ReportMeterDataDictionaryIndex
                            WHERE m.Name LIKE '%Electricity%Facility%'
                            AND m.ReportingFrequency = 'RunPeriod'
                        """)
                        result_electricity = cursor.fetchone()
                        
                        if result_electricity and result_electricity[0] and result_electricity[0] > 0:
                            # Value is in Joules, convert to kWh (1 kWh = 3,600,000 J)
                            total_joules = float(result_electricity[0])
                            energy_results = {
                                'total_electricity_kwh': total_joules / 3600000.0,
                                'total_site_energy_kwh': total_joules / 3600000.0  # Use as site energy
                            }
                        
                        # Also try to get building area from SQLite
                        if energy_results:
                            cursor.execute("""
                                SELECT SUM(Value) 
                                FROM ReportVariableData d
                                JOIN ReportVariableDataDictionary v ON d.ReportVariableDataDictionaryIndex = v.ReportVariableDataDictionaryIndex
                                WHERE v.Name LIKE '%Floor Area%'
                                AND v.ReportingFrequency = 'RunPeriod'
                                LIMIT 1
                            """)
                            area_result = cursor.fetchone()
                            if area_result and area_result[0] and area_result[0] > 0:
                                energy_results['building_area_m2'] = float(area_result[0])
                                if energy_results.get('total_site_energy_kwh'):
                                    energy_results['eui_kwh_m2'] = (
                                        energy_results['total_site_energy_kwh'] / 
                                        energy_results['building_area_m2']
                                    )
                        
                        conn.close()
                    except Exception as e:
                        pass
            
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

