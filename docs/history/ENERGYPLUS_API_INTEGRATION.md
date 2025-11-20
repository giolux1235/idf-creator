# EnergyPlus API Integration - Update Complete

## Changes Made

### Updated `/simulate` Endpoint in `web_interface.py`

The endpoint now uses a **hybrid approach**:

1. **First**: Tries to find local EnergyPlus executable
2. **If not found**: Automatically calls external EnergyPlus API at `https://web-production-1d1be.up.railway.app/simulate`

### Key Features

- ✅ **Automatic fallback**: No code changes needed in client applications
- ✅ **Transparent**: Returns same response format whether using local or external API
- ✅ **Metadata**: Response includes `used_external_api: true` when external API is used
- ✅ **Error handling**: Proper error messages if external API is unavailable
- ✅ **Configurable**: Can override API URL via `ENERGYPLUS_API_URL` environment variable

### Code Changes

**Location**: `web_interface.py` lines 499-543

**Before**: 
- If EnergyPlus not found → return error immediately

**After**:
- If EnergyPlus not found → call external EnergyPlus API
- Return results from external API (same format as local simulation)

### API Integration Details

**External API URL**: `https://web-production-1d1be.up.railway.app/simulate`

**Request Format** (same as local):
```json
{
  "idf_content": "...",
  "idf_filename": "building.idf",
  "weather_content": "base64_encoded_weather_file",
  "weather_filename": "weather.epw"
}
```

**Response Format** (same as local, with additional metadata):
```json
{
  "version": "33.0.0",
  "simulation_status": "success",
  "energyplus_version": "25.1.0",
  "real_simulation": true,
  "energy_results": {...},
  "warnings": [...],
  "used_external_api": true,
  "external_api_url": "https://web-production-1d1be.up.railway.app/simulate",
  "processing_time": "..."
}
```

---

## Deployment Status

### ✅ Code Updated Locally
- `web_interface.py` updated with external API integration
- Code ready to deploy

### ⏳ Needs Deployment
The changes need to be deployed to Railway for them to take effect on the production API.

**To Deploy**:
```bash
git add web_interface.py
git commit -m "Add external EnergyPlus API integration"
git push origin main
```

Railway will automatically deploy the changes.

---

## Testing

### Before Deployment
- Current test shows: "EnergyPlus executable not found" (expected - old code)

### After Deployment
- Test should show: Simulation runs via external API
- Response includes `used_external_api: true`

### Test Command
```bash
python test_api_comprehensive.py
```

Expected result after deployment:
- ✅ Full workflow test should PASS
- ✅ Simulation results should be returned
- ✅ Response should indicate external API was used

---

## Environment Variables

### Optional Configuration

Set `ENERGYPLUS_API_URL` environment variable in Railway to override the default:

```bash
ENERGYPLUS_API_URL=https://custom-energyplus-api.com/simulate
```

**Default**: `https://web-production-1d1be.up.railway.app/simulate`

---

## Benefits

1. **No Breaking Changes**: Existing clients continue to work
2. **Automatic**: No client code changes needed
3. **Scalable**: Can handle many simulation requests without installing EnergyPlus on main API server
4. **Flexible**: Can use local EnergyPlus if available, external API if not
5. **Cost Effective**: Separates IDF generation (lightweight) from simulation (resource-intensive)

---

## Architecture

```
Client Request
    ↓
web-production-3092c.up.railway.app/simulate
    ↓
Check for local EnergyPlus
    ↓
    ├─ Found → Run locally
    └─ Not Found → Forward to external API
                      ↓
          web-production-1d1be.up.railway.app/simulate
                      ↓
                  Return results
```

---

## Next Steps

1. ✅ Code updated locally
2. ⏳ Deploy to Railway (git push)
3. ⏳ Verify deployment successful
4. ⏳ Re-run comprehensive test
5. ⏳ Verify full workflow works end-to-end

---

## Notes

- The external API is already tested and working
- The integration maintains the same request/response format
- No changes needed to client applications
- The main API server (IDF generator) doesn't need EnergyPlus installed anymore










