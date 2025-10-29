#!/usr/bin/env python3
"""
REST API Server for IDF Creator
Simple API endpoints for IDF file generation
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import sys
import tempfile
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.nlp_building_parser import BuildingDescriptionParser
from src.document_parser import DocumentParser
from main import IDFCreator

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'IDF Creator API',
        'version': '1.0.0'
    })

@app.route('/api/generate', methods=['POST'])
def generate_idf():
    """
    Generate IDF file from parameters
    
    Request body (JSON):
    {
        "address": "123 Main St, City, State",
        "description": "Building description in natural language",
        "user_params": {
            "building_type": "office",
            "stories": 5,
            "floor_area": 75000
        },
        "llm_provider": "openai",  // optional: "none", "openai", "anthropic"
        "llm_api_key": "sk-...",   // optional
        "documents": []             // optional: list of base64 files or URLs
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Extract parameters
        address = data.get('address')
        description = data.get('description')
        user_params = data.get('user_params', {})
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
            extracted_params = result['idf_parameters']
            
            # Merge with user_params (user_params take precedence)
            user_params = {**extracted_params, **user_params}
        
        # Generate IDF
        creator = IDFCreator(enhanced=True, professional=True)
        
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
            'download_url': f'/api/download/{output_file}',
            'parameters_used': user_params
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'type': type(e).__name__
        }), 500

@app.route('/api/download/<filename>', methods=['GET'])
def download_idf(filename):
    """Download generated IDF file"""
    file_path = Path('artifacts/desktop_files/idf') / filename
    if file_path.exists():
        return send_file(file_path, as_attachment=True)
    return jsonify({
        'success': False,
        'error': 'File not found'
    }), 404

@app.route('/api/parse', methods=['POST'])
def parse_description():
    """
    Parse natural language description without generating IDF
    
    Request body (JSON):
    {
        "description": "Building description",
        "llm_provider": "openai",
        "llm_api_key": "sk-..."
    }
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('description'):
            return jsonify({
                'success': False,
                'error': 'Description is required'
            }), 400
        
        llm_provider = data.get('llm_provider', 'none')
        llm_api_key = data.get('llm_api_key', None)
        
        use_llm = llm_provider != 'none' and llm_api_key
        nlp_parser = BuildingDescriptionParser(
            use_llm=use_llm,
            llm_provider=llm_provider if use_llm else 'openai',
            api_key=llm_api_key
        )
        
        result = nlp_parser.parse_description(data['description'])
        
        return jsonify({
            'success': True,
            'parameters': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/documentation', methods=['GET'])
def documentation():
    """API documentation"""
    return jsonify({
        'name': 'IDF Creator API',
        'version': '1.0.0',
        'endpoints': {
            'GET /api/health': 'Health check',
            'POST /api/generate': 'Generate IDF file',
            'GET /api/download/<filename>': 'Download IDF file',
            'POST /api/parse': 'Parse building description',
            'GET /api/documentation': 'This documentation'
        },
        'example_request': {
            'url': '/api/generate',
            'method': 'POST',
            'body': {
                'address': '123 Main St, City, State',
                'description': '5-story office building, 75000 sq ft, VAV HVAC',
                'user_params': {
                    'building_type': 'office',
                    'stories': 5,
                    'floor_area': 75000
                }
            }
        }
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    
    print("🌐 Starting IDF Creator API Server...")
    print(f"📡 API running on http://localhost:{port}")
    print(f"📚 Documentation: http://localhost:{port}/api/documentation")
    print(f"💚 Health check: http://localhost:{port}/api/health")
    
    app.run(debug=True, host='0.0.0.0', port=port)

