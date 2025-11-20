# Geocoding Fix Applied - Request Parsing Bug

**Date**: 2025-11-04  
**Status**: ✅ **FIXED**

## 🐛 Issue Identified

The `/generate` endpoint was only handling form data requests (`request.form`), but tests were sending JSON payloads. This caused the service to receive `address 'None'` for all JSON requests, resulting in geocoding failures.

### Symptom
- All JSON requests to `/generate` returned: `"Failed to geocode address 'None'"`
- Service could not extract address parameter from JSON request body
- Geocoding infrastructure was working correctly, but request parsing was broken

## ✅ Fix Applied

### Changes to `web_interface.py` - `/generate` endpoint

The endpoint now handles **both JSON and form data** requests:

1. **JSON Request Detection**: Uses `request.get_json(silent=True)` to detect JSON requests
2. **Address Extraction**: Properly extracts `address` from JSON with fallback to `description`
3. **Parameter Handling**: Supports both `user_params` object and direct parameters for JSON requests
4. **Error Formatting**: Returns consistent error format with `error`, `type`, and `message` fields
5. **Response Format**: Includes `download_url` and `parameters_used` for JSON requests (matching `/api/generate`)

### Key Changes

```python
# Before: Only handled form data
address = request.form.get('address')

# After: Handles both JSON and form data
json_data = request.get_json(silent=True)
if json_data:
    address = json_data.get('address')
    # Fallback to description if address not provided
    if not address and json_data.get('description'):
        address = json_data.get('description')
else:
    address = request.form.get('address')
```

## 🧪 Test Cases Now Supported

The fix supports all the test cases from the report:

1. ✅ **Standard JSON**: `{"address": "...", "building_type": "office", ...}`
2. ✅ **Address Only**: `{"address": "..."}`
3. ✅ **Description Only**: `{"description": "..."}` (used as address)
4. ✅ **Both Fields**: `{"address": "...", "description": "..."}`

## 📋 Request Formats

### JSON Request (Now Supported)
```bash
curl -X POST https://web-production-3092c.up.railway.app/generate \
  -H "Content-Type: application/json" \
  -d '{"address": "258 N Clark St, Chicago, IL 60610", "building_type": "office"}'
```

### Form Data Request (Still Supported)
```bash
curl -X POST https://web-production-3092c.up.railway.app/generate \
  -F "address=258 N Clark St, Chicago, IL 60610" \
  -F "description=Office building"
```

## ✅ Expected Behavior After Fix

1. **JSON requests** will correctly extract the `address` parameter
2. **Geocoding** will work with real addresses from JSON payloads
3. **Error messages** will be consistent and informative
4. **Response format** will include all necessary fields for API consumers

## 🔍 Verification

To verify the fix works:

1. Send a JSON request to `/generate` with an address
2. Check that the address is correctly extracted (no more "address 'None'" errors)
3. Verify geocoding succeeds with valid addresses
4. Confirm response includes `download_url` and `parameters_used` for JSON requests

## 📝 Notes

- The `/api/generate` endpoint was already working correctly (it was handling JSON properly)
- The fix maintains backward compatibility with form data requests
- Both endpoints now have consistent behavior for JSON requests
