# Developer Guide: Geocoding Error Handling

## 🎯 Overview

The IDF Creator service now **enforces real coordinates only**. If geocoding cannot find real coordinates for an address, the API will return a `400 Bad Request` error instead of using synthetic defaults.

---

## ⚠️ Breaking Changes

### Before (Old Behavior)
- System would fall back to Chicago coordinates (41.8781, -87.6298) if geocoding failed
- Requests would always succeed, even with invalid addresses
- IDF files could be generated with incorrect location data

### After (Current Behavior)
- System raises `GeocodingError` if no real coordinates found
- API returns `400 Bad Request` for geocoding failures
- IDF files are always generated with accurate location data

---

## 🔧 API Changes

### Error Response Format

**Geocoding Error (400 Bad Request):**
```json
{
  "success": false,
  "error": "Failed to geocode address 'Invalid Address XYZ'. Could not find real coordinates from any source (lookup table, Google Maps API, or Nominatim). Please provide a valid address with city and state information.",
  "type": "GeocodingError",
  "message": "Geocoding failed: Could not find real coordinates for the provided address. Please provide a valid address with city and state information."
}
```

### HTTP Status Codes

| Status Code | Meaning | Action |
|-------------|---------|--------|
| 200 | Success | Process response normally |
| 400 | Bad Request | Geocoding failed - check address format |
| 500 | Server Error | Internal error - retry or contact support |

---

## 📝 Required Address Format

### ✅ Valid Address Formats

```javascript
// Format 1: Full street address
"147 Sutter St, San Francisco, CA 94104"

// Format 2: City and state only
"San Francisco, CA"

// Format 3: City and state with ZIP
"San Francisco, CA 94104"

// Format 4: Street address with city and state
"123 Main St, New York, NY"
```

### ❌ Invalid Address Formats

```javascript
// Missing city/state
"123 Main St"  // ❌ Will raise GeocodingError

// Missing state
"123 Main St, San Francisco"  // ❌ May fail geocoding

// Empty address
""  // ❌ Will raise GeocodingError

// Invalid format
"Some random text"  // ❌ Will raise GeocodingError
```

---

## 💻 Code Examples

### JavaScript/TypeScript

```javascript
async function generateIDF(address, description) {
  try {
    const response = await fetch('https://your-api-url.railway.app/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        address: address,
        description: description
      })
    });
    
    const result = await response.json();
    
    if (response.status === 400 && result.type === 'GeocodingError') {
      // Handle geocoding error specifically
      console.error('Geocoding failed:', result.error);
      alert('Invalid address. Please provide a valid address with city and state.');
      return null;
    }
    
    if (!result.success) {
      throw new Error(result.error);
    }
    
    return result;
  } catch (error) {
    console.error('Request failed:', error);
    throw error;
  }
}

// Usage with error handling
generateIDF('123 Main St, San Francisco, CA')
  .then(result => {
    if (result) {
      console.log('✅ IDF generated:', result);
    }
  })
  .catch(error => {
    console.error('❌ Error:', error);
  });
```

### Python

```python
import requests
from typing import Optional, Dict

def generate_idf(address: str, description: Optional[str] = None) -> Optional[Dict]:
    """
    Generate IDF file with proper error handling.
    
    Args:
        address: Building address (must include city and state)
        description: Optional building description
    
    Returns:
        Response dictionary if successful, None if geocoding failed
    
    Raises:
        requests.HTTPError: For server errors (500)
    """
    url = "https://your-api-url.railway.app/api/generate"
    
    payload = {"address": address}
    if description:
        payload["description"] = description
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raises for 4xx and 5xx
        
        result = response.json()
        
        if result.get('success'):
            return result
        else:
            error_type = result.get('type', 'Unknown')
            if error_type == 'GeocodingError':
                print(f"❌ Geocoding failed: {result.get('error')}")
                print("   Please provide a valid address with city and state.")
                return None
            else:
                raise Exception(f"Error: {result.get('error')}")
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            # Geocoding error
            result = e.response.json()
            print(f"❌ Geocoding failed: {result.get('error')}")
            return None
        else:
            # Other HTTP errors
            raise
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        raise

# Usage
result = generate_idf("147 Sutter St, San Francisco, CA 94104")
if result:
    print("✅ IDF generated successfully!")
else:
    print("❌ Geocoding failed. Please check the address format.")
```

### React/Next.js

```jsx
import { useState } from 'react';

function IDFGenerator() {
  const [address, setAddress] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  
  const handleGenerate = async () => {
    setError(null);
    setLoading(true);
    
    try {
      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address })
      });
      
      const result = await response.json();
      
      if (response.status === 400 && result.type === 'GeocodingError') {
        setError(`Geocoding failed: ${result.message}`);
        return;
      }
      
      if (!result.success) {
        setError(result.error || 'Unknown error');
        return;
      }
      
      // Success - handle result
      console.log('IDF generated:', result);
      
    } catch (err) {
      setError(`Request failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div>
      <input
        type="text"
        value={address}
        onChange={(e) => setAddress(e.target.value)}
        placeholder="123 Main St, City, State ZIP"
      />
      
      <button onClick={handleGenerate} disabled={loading}>
        {loading ? 'Generating...' : 'Generate IDF'}
      </button>
      
      {error && (
        <div className="error">
          <p>❌ {error}</p>
          <p>Please ensure the address includes city and state.</p>
        </div>
      )}
    </div>
  );
}
```

---

## ✅ Best Practices

### 1. Validate Address Before Sending

```javascript
function validateAddress(address) {
  if (!address || address.trim().length === 0) {
    return { valid: false, error: 'Address is required' };
  }
  
  // Check for city and state (basic validation)
  const hasComma = address.includes(',');
  const parts = address.split(',');
  
  if (!hasComma || parts.length < 2) {
    return {
      valid: false,
      error: 'Address must include city and state (e.g., "City, State")'
    };
  }
  
  // Check for state abbreviation (2 uppercase letters)
  const stateMatch = address.match(/\b[A-Z]{2}\b/);
  if (!stateMatch) {
    return {
      valid: false,
      error: 'Address should include state abbreviation (e.g., CA, NY, TX)'
    };
  }
  
  return { valid: true };
}

// Use before API call
const validation = validateAddress(userInput);
if (!validation.valid) {
  alert(validation.error);
  return;
}
```

### 2. Handle Errors Gracefully

```javascript
async function generateIDFWithRetry(address, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const result = await generateIDF(address);
      return result;
    } catch (error) {
      if (error.response?.status === 400) {
        // Geocoding error - don't retry, just return error
        return { error: error.response.data.error };
      }
      
      if (attempt === maxRetries) {
        throw error;
      }
      
      // Wait before retry (exponential backoff)
      await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
    }
  }
}
```

### 3. Provide User-Friendly Error Messages

```javascript
function getUserFriendlyError(error) {
  if (error.type === 'GeocodingError') {
    return 'Could not find the location for this address. Please check:\n' +
           '• Address includes city and state\n' +
           '• Format: "Street, City, State ZIP"\n' +
           '• Example: "123 Main St, San Francisco, CA"';
  }
  
  return error.message || 'An unexpected error occurred';
}
```

---

## 🧪 Testing

### Test Cases

```javascript
// Test 1: Valid address
await generateIDF('147 Sutter St, San Francisco, CA 94104');
// Expected: ✅ Success

// Test 2: City and state only
await generateIDF('San Francisco, CA');
// Expected: ✅ Success (uses lookup table)

// Test 3: Invalid address
await generateIDF('Invalid Address XYZ');
// Expected: ❌ 400 GeocodingError

// Test 4: Empty address
await generateIDF('');
// Expected: ❌ 400 GeocodingError

// Test 5: Missing state
await generateIDF('123 Main St, San Francisco');
// Expected: ⚠️ May fail depending on geocoding service
```

---

## 📊 Error Types

### GeocodingError (400)
- **Cause**: Address cannot be geocoded
- **Solution**: Provide valid address with city and state
- **Retry**: No - fix the address first

### Server Error (500)
- **Cause**: Internal server error
- **Solution**: Retry request or contact support
- **Retry**: Yes - with exponential backoff

---

## 🔗 Related Documentation

- **API Documentation**: See `API_DOCUMENTATION.md`
- **Geocoding Details**: See `GEOCODING_REAL_COORDINATES_ENFORCEMENT.md`
- **Supported Cities**: See `API_DOCUMENTATION.md` (Geocoding section)

---

## ✅ Migration Checklist

- [ ] Update error handling to check for `GeocodingError` type
- [ ] Validate address format before sending requests
- [ ] Update user-facing error messages
- [ ] Test with invalid addresses to ensure proper error handling
- [ ] Update documentation/user guides with address format requirements

---

**Last Updated**: 2025-01-04  
**Version**: 1.0.0

