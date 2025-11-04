# IDF Creator API Documentation

Complete integration guide for developers to integrate IDF Creator into their applications.

## 🌐 Base URL

### Local Development
```
http://localhost:5000/api
```

### Production (Railway)
```
https://your-app.railway.app/api
```

---

## 📋 API Endpoints

### 1. Health Check
**GET** `/api/health`

Check if the API is running and healthy.

**Request:**
```bash
GET /api/health
```

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

Generate an EnergyPlus IDF file from building parameters and address.

**Request:**
```bash
POST /api/generate
Content-Type: application/json
```

**Request Body:**
```json
{
  "address": "147 Sutter St, San Francisco, CA 94104",
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

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `address` | string | ✅ Yes | Building address (used for geocoding) |
| `description` | string | No | Natural language building description |
| `user_params` | object | No | Explicit building parameters |
| `user_params.building_type` | string | No | Building type (office, retail, residential, etc.) |
| `user_params.stories` | integer | No | Number of floors |
| `user_params.floor_area` | number | No | Total floor area in square feet |
| `user_params.floor_area_per_story_m2` | number | No | Floor area per story in square meters |
| `llm_provider` | string | No | LLM provider: "none", "openai", or "anthropic" |
| `llm_api_key` | string | No | API key for LLM provider (if using AI parsing) |

**Success Response (200):**
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
  },
  "location_data": {
    "address": "147 Sutter St, San Francisco, CA 94104",
    "latitude": 37.7749,
    "longitude": -122.4194,
    "time_zone": -8.0,
    "elevation": 2
  }
}
```

**Error Response (400):**
```json
{
  "success": false,
  "error": "Failed to geocode address 'Invalid Address XYZ'. Could not find real coordinates from any source (lookup table, Google Maps API, or Nominatim). Please provide a valid address with city and state information.",
  "type": "GeocodingError",
  "message": "Geocoding failed: Could not find real coordinates for the provided address. Please provide a valid address with city and state information."
}
```

**Error Response (500):**
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

**Request:**
```bash
GET /api/download/Office_api.idf
```

**Response:** Binary IDF file download

---

## 🌍 Geocoding & Location Services

The IDF Creator uses a **hybrid geocoding approach** for optimal performance and cost:

### Priority Order:
1. **Lookup Table** (50+ major US cities) - Fast, free, instant ⚡
2. **Google Maps API** (optional) - Accurate, requires API key, costs money 💰
3. **Nominatim API** (free) - OpenStreetMap geocoding, rate-limited
4. **Keyword Detection** - Backup for common city names
5. **Error** - Raises `GeocodingError` if no real coordinates found

**⚠️ Important:** The system now **enforces real coordinates only**. If geocoding cannot find real coordinates for an address, the API will return a `400 Bad Request` error with a clear message. No synthetic defaults are used.

### Supported Cities (Lookup Table)
50+ major US cities are supported instantly via lookup table:
- San Francisco, CA
- New York, NY
- Los Angeles, CA
- Chicago, IL
- Seattle, WA
- Houston, TX
- Miami, FL
- And 43+ more...

**Benefits:**
- ✅ Instant geocoding (0-1ms vs 50-200ms)
- ✅ Zero cost for major cities
- ✅ 100% reliability (works offline)
- ✅ No rate limits

### Google Maps API (Optional)

To use Google Maps API for more accurate geocoding:

1. **Get Google Maps API Key:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a project and enable Geocoding API
   - Create an API key

2. **Set Environment Variable:**
   ```bash
   export GOOGLE_MAPS_API_KEY="your-api-key-here"
   ```

3. **Cost:** ~$5 per 1,000 requests (after free tier)

**When Google Maps is used:**
- Addresses not in the lookup table (50+ cities)
- More accurate coordinates for specific street addresses
- Falls back to Nominatim if Google API fails

---

## 💻 Integration Examples

### JavaScript/TypeScript (Fetch API)

```javascript
// Generate IDF File
async function generateIDF(address, description, apiKey) {
  try {
    const response = await fetch('https://your-railway-url.railway.app/api/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        address: address,
        description: description,
        user_params: {
          building_type: 'office',
          stories: 5,
          floor_area: 75000
        },
        llm_provider: 'openai',
        llm_api_key: apiKey  // Optional: user provides their own key
      })
    });
    
    const result = await response.json();
    
    if (result.success) {
      console.log('IDF generated successfully!');
      console.log('Location:', result.location_data);
      
      // Download the file
      const downloadUrl = `https://your-railway-url.railway.app${result.download_url}`;
      window.location.href = downloadUrl;
      
      return result;
    } else {
      console.error('Error:', result.error);
      throw new Error(result.error);
    }
  } catch (error) {
    console.error('Request failed:', error);
    throw error;
  }
}

// Usage
generateIDF(
  '147 Sutter St, San Francisco, CA 94104',
  '5-story office building with 75,000 sq ft, VAV HVAC',
  'sk-proj-...'  // Optional OpenAI API key
);
```

### React Component Example

```jsx
import React, { useState } from 'react';

function IDFGenerator() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  
  const API_BASE_URL = 'https://your-railway-url.railway.app/api';

  const generateIDF = async (address, description, apiKey) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          address: address,
          description: description,
          llm_provider: apiKey ? 'openai' : 'none',
          llm_api_key: apiKey
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setResult(data);
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <input 
        type="text" 
        placeholder="Building Address" 
        id="address"
      />
      <textarea 
        placeholder="Building Description" 
        id="description"
      />
      <input 
        type="password" 
        placeholder="OpenAI API Key (Optional)" 
        id="apiKey"
      />
      
      <button 
        onClick={() => generateIDF(
          document.getElementById('address').value,
          document.getElementById('description').value,
          document.getElementById('apiKey').value
        )}
        disabled={loading}
      >
        {loading ? 'Generating...' : 'Generate IDF'}
      </button>
      
      {error && <div className="error">{error}</div>}
      
      {result?.success && (
        <div className="success">
          <p>✅ IDF Generated!</p>
          <p>Location: {result.location_data?.latitude}°N, {result.location_data?.longitude}°W</p>
          <a href={`${API_BASE_URL}${result.download_url}`}>
            Download IDF File
          </a>
        </div>
      )}
    </div>
  );
}
```

### Python (Requests Library)

```python
import requests
import os

# API Configuration
API_BASE_URL = "https://your-railway-url.railway.app/api"

def generate_idf(address, description=None, user_params=None, llm_api_key=None):
    """
    Generate IDF file from building address and parameters.
    
    Args:
        address: Building address (required)
        description: Natural language description (optional)
        user_params: Dictionary of explicit parameters (optional)
        llm_api_key: OpenAI or Anthropic API key (optional)
    
    Returns:
        Dictionary with success status and download URL
    """
    url = f"{API_BASE_URL}/generate"
    
    payload = {
        "address": address,
    }
    
    if description:
        payload["description"] = description
    
    if user_params:
        payload["user_params"] = user_params
    
    if llm_api_key:
        payload["llm_provider"] = "openai"
        payload["llm_api_key"] = llm_api_key
    
    response = requests.post(url, json=payload)
    response.raise_for_status()
    
    result = response.json()
    
    if result.get('success'):
        print(f"✅ IDF generated successfully!")
        print(f"Location: {result['location_data']['latitude']:.4f}°N, "
              f"{result['location_data']['longitude']:.4f}°W")
        print(f"Download URL: {API_BASE_URL}{result['download_url']}")
        return result
    else:
        raise Exception(f"Error: {result.get('error', 'Unknown error')}")

# Usage Examples
if __name__ == "__main__":
    # Example 1: Simple address
    result = generate_idf("147 Sutter St, San Francisco, CA 94104")
    
    # Example 2: With description
    result = generate_idf(
        address="123 Broadway, New York, NY 10001",
        description="5-story office building with 75,000 sq ft, VAV HVAC"
    )
    
    # Example 3: With explicit parameters
    result = generate_idf(
        address="456 Sunset Blvd, Los Angeles, CA 90028",
        user_params={
            "building_type": "office",
            "stories": 5,
            "floor_area": 75000
        }
    )
    
    # Example 4: With AI parsing (requires API key)
    result = generate_idf(
        address="500 Pine St, Seattle, WA 98101",
        description="Modern office tower with rooftop HVAC and LED lighting",
        llm_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Download the file
    if result.get('success'):
        download_url = f"{API_BASE_URL}{result['download_url']}"
        file_response = requests.get(download_url)
        
        with open(result['filename'], 'wb') as f:
            f.write(file_response.content)
        
        print(f"✅ File saved as {result['filename']}")
```

### cURL Examples

```bash
# Basic request with address only
curl -X POST https://your-railway-url.railway.app/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "address": "147 Sutter St, San Francisco, CA 94104"
  }'

# With building description
curl -X POST https://your-railway-url.railway.app/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "address": "123 Broadway, New York, NY 10001",
    "description": "5-story office building with 75,000 sq ft, VAV HVAC system"
  }'

# With explicit parameters
curl -X POST https://your-railway-url.railway.app/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "address": "456 Sunset Blvd, Los Angeles, CA 90028",
    "user_params": {
      "building_type": "office",
      "stories": 5,
      "floor_area": 75000
    }
  }'

# Download the generated file
curl -O https://your-railway-url.railway.app/api/download/Office_api.idf
```

---

## 🔑 API Keys & Configuration

### Optional: Google Maps API

For more accurate geocoding (especially for addresses not in major cities):

1. Get API key from [Google Cloud Console](https://console.cloud.google.com/)
2. Enable "Geocoding API"
3. Set environment variable on server:
   ```bash
   export GOOGLE_MAPS_API_KEY="your-key-here"
   ```

**Note:** This is optional. The service works perfectly without it using the lookup table and Nominatim.

### Optional: LLM API Keys (OpenAI/Anthropic)

For AI-powered natural language parsing:

- **OpenAI**: Get key from https://platform.openai.com/api-keys
- **Anthropic**: Get key from https://console.anthropic.com/

Users can provide their own API keys in the request, or you can set them as environment variables on the server.

---

## 📝 Response Format

All responses follow a consistent format:

### Success Response
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { ... }
}
```

### Error Response
```json
{
  "success": false,
  "error": "Human-readable error message",
  "type": "ExceptionType"
}
```

---

## 🚨 Error Handling

### HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Process response |
| 400 | Bad Request | Check request parameters |
| 404 | Not Found | Check endpoint URL |
| 500 | Server Error | Retry or contact support |

### Common Errors

**Missing Address:**
```json
{
  "success": false,
  "error": "Address is required"
}
```

**Geocoding Error (400 Bad Request):**
```json
{
  "success": false,
  "error": "Failed to geocode address 'Invalid Address XYZ'. Could not find real coordinates from any source (lookup table, Google Maps API, or Nominatim). Please provide a valid address with city and state information.",
  "type": "GeocodingError",
  "message": "Geocoding failed: Could not find real coordinates for the provided address. Please provide a valid address with city and state information."
}
```

**Common Geocoding Errors:**
- Empty address provided
- Invalid address format (missing city/state)
- Address that cannot be geocoded by any source
- Invalid coordinates returned from API (0,0, out of range, etc.)

**How to Fix:**
- Ensure address includes city and state (e.g., "123 Main St, San Francisco, CA")
- Use standard address format: "Street, City, State ZIP"
- For US addresses, include state abbreviation (CA, NY, TX, etc.)

**Generation Failed:**
```json
{
  "success": false,
  "error": "Failed to generate IDF file: [reason]"
}
```

---

## 🔐 Security & Best Practices

### 1. API Key Handling
- **Don't** hardcode API keys in client-side code
- **Do** let users provide their own API keys (LLM keys)
- **Do** store Google Maps API key as environment variable on server

### 2. CORS
- CORS is enabled for all origins by default
- Configure specific origins in production for better security

### 3. Rate Limiting
- Lookup table: Unlimited (instant)
- Google Maps API: Subject to Google's rate limits
- Nominatim: 1 request per second (free tier)

### 4. Error Handling
- Always check `success` field in response
- Handle network errors gracefully
- Implement retry logic for transient failures

---

## 🚀 Deployment

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Start server
python web_interface.py

# Server runs on http://localhost:5000
```

### Railway Deployment
1. Push code to GitHub
2. Connect repository to Railway
3. Railway automatically detects `Procfile` and deploys
4. Get your Railway URL from dashboard

**Procfile:**
```
web: python web_interface.py
```

---

## 📊 Geocoding Performance

### Performance Metrics

| Method | Speed | Cost | Reliability |
|--------|-------|------|-------------|
| Lookup Table | 0-1ms | Free | 100% |
| Google Maps API | 50-200ms | $5/1K | 99.9% |
| Nominatim API | 100-300ms | Free | 99% |

### Cost Example (10,000 requests/month)

**Without Google Maps:**
- 8,000 major cities → Lookup table: $0
- 2,000 other addresses → Nominatim: $0
- **Total: $0/month**

**With Google Maps:**
- 8,000 major cities → Lookup table: $0
- 2,000 other addresses → Google Maps: ~$10
- **Total: ~$10/month**

---

## 🆘 Support & Troubleshooting

### Health Check
Always check the health endpoint first:
```bash
GET /api/health
```

### Common Issues

**Issue: Geocoding Error (400 Bad Request)**
- ✅ **Required**: Address must include city and state (e.g., "123 Main St, San Francisco, CA")
- ✅ Check if city is in lookup table (50+ major cities supported)
- ✅ Verify address format: "Street, City, State ZIP" or "City, State"
- ✅ For US addresses, include state abbreviation (CA, NY, TX, IL, etc.)
- ✅ Optional: Set `GOOGLE_MAPS_API_KEY` for more accurate geocoding
- ❌ **No fallback**: System will return error if address cannot be geocoded (no synthetic defaults)

**Issue: Slow geocoding**
- ✅ Major cities use lookup table (instant)
- ✅ Other addresses may take 100-300ms (using Nominatim)
- ✅ Consider Google Maps API for faster geocoding

**Issue: API key errors**
- ✅ Google Maps API key: Check environment variable
- ✅ LLM API keys: Check if provided in request or environment

---

## 📚 Additional Resources

- **Full Documentation**: See `README.md`
- **Developer Geocoding Guide**: See `DEVELOPER_GEOCODING_GUIDE.md` (⚠️ Important: Error handling)
- **Geocoding Enforcement**: See `GEOCODING_REAL_COORDINATES_ENFORCEMENT.md`
- **Geocoding Details**: See `docs/WHY_LOOKUP_TABLE.md`
- **Example Code**: See `example.py`
- **GitHub**: https://github.com/giolux1235/idf-creator

---

## ✅ Quick Integration Checklist

- [ ] Get Railway URL (or use localhost for development)
- [ ] Test health endpoint: `GET /api/health`
- [ ] Make test request: `POST /api/generate` with address
- [ ] Handle success/error responses
- [ ] Download IDF file from `download_url`
- [ ] (Optional) Set `GOOGLE_MAPS_API_KEY` for better geocoding
- [ ] (Optional) Support LLM API keys from users

---

**Version**: 1.0.0  
**Last Updated**: 2025-01-04  
**Status**: ✅ Production Ready

