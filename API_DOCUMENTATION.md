# IDF Creator API Documentation

## 🌐 Base URL
```
http://localhost:5001/api
```
Or on Railway:
```
https://your-app.railway.app/api
```

## 📋 Endpoints

### 1. Health Check
**GET** `/api/health`

Check if the API is running.

**Response:**
```json
{
  "status": "healthy",
  "service": "IDF Creator API",
  "version": "1.0.0"
}
```

---

### 2. Generate IDF File
**POST** `/api/generate`

Generate an EnergyPlus IDF file from building parameters.

**Request Body:**
```json
{
  "address": "123 Main St, Seattle, WA 98101",
  "description": "A modern 5-story office building with 75,000 sq ft, VAV HVAC system",
  "user_params": {
    "building_type": "office",
    "stories": 5,
    "floor_area": 75000
  },
  "llm_provider": "openai",
  "llm_api_key": "sk-proj-..."
}
```

**Parameters:**
- `address` (required): Building address
- `description` (optional): Natural language description
- `user_params` (optional): Explicit parameters
  - `building_type`: office, retail, residential, school, hospital, etc.
  - `stories`: Number of floors
  - `floor_area`: Total floor area in square feet
- `llm_provider` (optional): "none", "openai", or "anthropic"
- `llm_api_key` (optional): API key for LLM provider

**Success Response:**
```json
{
  "success": true,
  "message": "IDF file generated successfully",
  "filename": "Office_api.idf",
  "download_url": "/api/download/Office_api.idf",
  "parameters_used": {
    "building_type": "Office",
    "stories": 5,
    "floor_area": 75000.0
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Error message",
  "type": "ExceptionType"
}
```

---

### 3. Download IDF File
**GET** `/api/download/<filename>`

Download a previously generated IDF file.

**Example:**
```
GET /api/download/Office_api.idf
```

**Response:** IDF file download

---

### 4. Parse Description
**POST** `/api/parse`

Parse a building description without generating an IDF file.

**Request Body:**
```json
{
  "description": "5-story office building, 75,000 sq ft, VAV HVAC",
  "llm_provider": "openai",
  "llm_api_key": "sk-proj-..."
}
```

**Success Response:**
```json
{
  "success": true,
  "parameters": {
    "building_type": "Office",
    "stories": 5,
    "floor_area": 75000.0,
    "hvac_system_type": "vav"
  }
}
```

---

## 💻 Usage Examples

### JavaScript/TypeScript (Fetch API)

```javascript
// Generate IDF
async function generateIDF() {
  const response = await fetch('http://localhost:5001/api/generate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      address: '600 Pine Street, Seattle, WA 98101',
      description: 'A modern 5-story office building with VAV HVAC',
      llm_provider: 'openai',
      llm_api_key: 'sk-proj-...'
    })
  });
  
  const result = await response.json();
  
  if (result.success) {
    // Download the IDF file
    window.location.href = result.download_url;
  }
}
```

### Python (Requests)

```python
import requests

# Generate IDF
url = 'http://localhost:5001/api/generate'
data = {
    'address': '600 Pine Street, Seattle, WA 98101',
    'description': 'A modern 5-story office building with VAV HVAC',
    'user_params': {
        'building_type': 'office',
        'stories': 5,
        'floor_area': 75000
    },
    'llm_provider': 'openai',
    'llm_api_key': 'sk-proj-...'
}

response = requests.post(url, json=data)
result = response.json()

if result['success']:
    # Download the file
    download_url = result['download_url']
    file_response = requests.get(download_url)
    
    with open('building.idf', 'wb') as f:
        f.write(file_response.content)
```

### cURL

```bash
# Generate IDF
curl -X POST http://localhost:5001/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "address": "600 Pine Street, Seattle, WA 98101",
    "description": "5-story office building with 75,000 sq ft",
    "llm_provider": "openai",
    "llm_api_key": "sk-proj-..."
  }'

# Download IDF
curl -O http://localhost:5001/api/download/Office_api.idf
```

---

## 🚀 Running the API

### Local Development
```bash
python web_interface.py
```

The API will run on `http://localhost:5001`

### Railway Deployment
Update your `Procfile`:
```
web: python web_interface.py
```

Note: `web_interface.py` provides both web UI and API endpoints

---

## 📝 Error Handling

All endpoints return consistent error responses:
```json
{
  "success": false,
  "error": "Error message",
  "type": "ExceptionType"
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad Request (missing required parameters)
- `404`: Not Found (file or endpoint)
- `500`: Internal Server Error

---

## 🔐 Security Notes

1. **API Keys**: LLM API keys are sent from your app but not stored on the server
2. **CORS**: Enabled for all origins (configure in production)
3. **File Persistence**: Generated IDF files are stored temporarily (configure cleanup)

---

## 📚 Full Example Integration

### React Component

```jsx
import React, { useState } from 'react';

function IDFGenerator() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const generateIDF = async () => {
    setLoading(true);
    
    try {
      const response = await fetch('http://localhost:5001/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          address: '600 Pine St, Seattle, WA',
          description: document.getElementById('description').value,
          llm_provider: 'openai',
          llm_api_key: document.getElementById('apiKey').value
        })
      });
      
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <textarea id="description" placeholder="Describe your building..." />
      <input id="apiKey" type="password" placeholder="OpenAI API Key" />
      <button onClick={generateIDF} disabled={loading}>
        {loading ? 'Generating...' : 'Generate IDF'}
      </button>
      
      {result?.success && (
        <a href={result.download_url}>Download IDF File</a>
      )}
    </div>
  );
}
```

---

## 🆘 Support

For issues or questions:
- Check the health endpoint: `GET /api/health`
- Review error messages in API responses
- Check server logs for detailed debugging

