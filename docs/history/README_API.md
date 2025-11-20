# IDF Creator - Simple Integration Guide for Your Web App

## 🎯 What You Need to Know

Your web app needs to make HTTP requests to the IDF Creator API running on Railway.

---

## 📍 Step 1: Get Your Railway URL

After deploying on Railway, you'll get a URL like:
```
https://idf-creator-production.up.railway.app
```

---

## 📝 Step 2: Make API Calls from Your Web App

### The Main Endpoint: Generate IDF File

**URL:** `https://your-railway-url.railway.app/api/generate`  
**Method:** `POST`  
**Content-Type:** `application/json`

---

## 💻 Examples for Your Web App

### Example 1: JavaScript/React (Fetch API)

```javascript
async function generateIDF() {
  try {
    const response = await fetch('https://your-railway-url.railway.app/api/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        address: '600 Pine Street, Seattle, WA 98101',
        description: 'A modern 5-story office building with VAV HVAC system',
        llm_provider: 'openai',
        llm_api_key: 'sk-proj-...'  // User provides this
      })
    });
    
    const data = await response.json();
    
    if (data.success) {
      // Download the IDF file
      window.location.href = data.download_url;
    } else {
      console.error('Error:', data.error);
    }
  } catch (error) {
    console.error('Request failed:', error);
  }
}
```

### Example 2: React Component with Form

```jsx
import React, { useState } from 'react';

function IDFGeneratorForm() {
  const [description, setDescription] = useState('');
  const [address, setAddress] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await fetch('https://your-railway-url.railway.app/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          address: address,
          description: description,
          llm_provider: 'openai',
          llm_api_key: apiKey
        })
      });
      
      const data = await response.json();
      setResult(data);
      
      if (data.success) {
        // Auto-download the file
        window.open(data.download_url, '_blank');
      }
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        placeholder="Building Address"
        value={address}
        onChange={(e) => setAddress(e.target.value)}
        required
      />
      
      <textarea
        placeholder="Describe your building..."
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        required
      />
      
      <input
        type="password"
        placeholder="OpenAI API Key (optional)"
        value={apiKey}
        onChange={(e) => setApiKey(e.target.value)}
      />
      
      <button type="submit" disabled={loading}>
        {loading ? 'Generating...' : 'Generate IDF File'}
      </button>
      
      {result?.error && <div className="error">{result.error}</div>}
    </form>
  );
}

export default IDFGeneratorForm;
```

### Example 3: Python Backend (Flask/FastAPI)

```python
import requests

def generate_idf(description, address, api_key=None):
    url = 'https://your-railway-url.railway.app/api/generate'
    
    data = {
        'address': address,
        'description': description,
    }
    
    if api_key:
        data['llm_provider'] = 'openai'
        data['llm_api_key'] = api_key
    
    response = requests.post(url, json=data)
    result = response.json()
    
    if result['success']:
        # Download the file
        file_response = requests.get(result['download_url'])
        return file_response.content
    else:
        raise Exception(result['error'])

# Usage
idf_content = generate_idf(
    description='5-story office building',
    address='600 Pine St, Seattle, WA',
    api_key='sk-proj-...'
)
```

### Example 4: Simple HTML Form

```html
<!DOCTYPE html>
<html>
<head>
    <title>IDF Generator</title>
</head>
<body>
    <form id="idfForm">
        <input type="text" id="address" placeholder="Building Address" required>
        <br><br>
        <textarea id="description" placeholder="Describe your building..." required></textarea>
        <br><br>
        <input type="password" id="apiKey" placeholder="OpenAI API Key (optional)">
        <br><br>
        <button type="submit">Generate IDF</button>
    </form>
    
    <script>
        document.getElementById('idfForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const data = {
                address: document.getElementById('address').value,
                description: document.getElementById('description').value,
                llm_provider: 'openai',
                llm_api_key: document.getElementById('apiKey').value
            };
            
            const response = await fetch('https://your-railway-url.railway.app/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.success) {
                window.location.href = result.download_url;
            } else {
                alert('Error: ' + result.error);
            }
        });
    </script>
</body>
</html>
```

---

## 🎯 Minimal Request Format

```json
{
  "address": "Building address",
  "description": "Building description in natural language"
}
```

**With AI enhancement (optional):**
```json
{
  "address": "Building address",
  "description": "Building description",
  "llm_provider": "openai",
  "llm_api_key": "sk-proj-..."
}
```

---

## 📥 Response Format

**Success:**
```json
{
  "success": true,
  "message": "IDF file generated successfully",
  "filename": "Office_api.idf",
  "download_url": "/api/download/Office_api.idf",
  "parameters_used": { ... }
}
```

**Error:**
```json
{
  "success": false,
  "error": "Error message"
}
```

---

## 🔑 API Key Handling

**Option 1:** Let users provide their own API key (recommended)
- User pastes their OpenAI API key
- Pass it in the request
- No cost to you!

**Option 2:** Use your own API key
- Set it in your backend
- Users don't need to provide keys
- You pay for API usage

---

## ✅ Summary

**To integrate IDF Creator into your web app, you need:**

1. ✅ The Railway URL (get from Railway dashboard)
2. ✅ Make POST request to `/api/generate`
3. ✅ Send `address` and `description` (required)
4. ✅ Optionally send `llm_api_key` for AI features
5. ✅ Download the file from `download_url` in response

**That's it!** No special libraries or SDKs needed - just HTTP requests! 🎉

