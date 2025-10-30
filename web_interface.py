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
            'building_type': idf_params.get('building_type')
        }
        
        # Create temporary output file
        temp_dir = tempfile.mkdtemp()
        building_name = user_params.get('building_type', 'Building').replace(' ', '_')
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
            'building_type': idf_params.get('building_type')
        }
        
        # Generate output filename
        building_name = idf_params.get('building_type', 'Building').replace(' ', '_')
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

