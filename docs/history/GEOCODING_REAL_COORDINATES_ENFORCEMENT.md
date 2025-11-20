# Geocoding Real Coordinates Enforcement

## ✅ Changes Applied

The geocoding system now **enforces real coordinates only**. If geocoding cannot find real coordinates for an address, it will raise a `GeocodingError` instead of using synthetic defaults.

---

## 🔧 Changes Made

### 1. Created `GeocodingError` Exception
- **Location**: `src/location_fetcher.py`
- **Purpose**: Custom exception raised when real coordinates cannot be found
- **Message**: Clear error message explaining that geocoding failed

### 2. Removed Chicago Default Fallback
- **Before**: System would fall back to Chicago coordinates (41.8781, -87.6298) if geocoding failed
- **After**: System raises `GeocodingError` if no real coordinates are found

### 3. Updated `geocode_address()` Method
- **Validation**: Now validates coordinates from API responses
  - Rejects (0,0) coordinates
  - Rejects coordinates outside valid range (lat > 90, lon > 180)
  - Rejects invalid US coordinates (positive longitude for US addresses)
- **Error Handling**: Raises `GeocodingError` instead of returning Chicago defaults

### 4. Updated `_geocode_fallback_final()` Method
- **Before**: Returned Chicago coordinates as ultimate fallback
- **After**: Raises `GeocodingError` if no real coordinates found from:
  - City lookup table
  - Keyword detection
  - API geocoding

### 5. Updated `fetch_location_data()` Method
- **Before**: Used Chicago default if geocoding failed
- **After**: Raises `GeocodingError` if:
  - Empty address provided
  - No coordinates found
  - Chicago coordinates detected for non-Chicago addresses

### 6. Updated `fetch_comprehensive_location_data()` Method
- **Before**: Used Chicago default if geocoding failed
- **After**: Raises `GeocodingError` if:
  - No coordinates found
  - Chicago coordinates detected for non-Chicago addresses

### 7. Updated Error Handling in `main.py`
- **Import**: Added `GeocodingError` import
- **Handling**: Existing exception handler will catch and display error

### 8. Updated Error Handling in `web_interface.py`
- **Import**: Added `GeocodingError` import
- **Handling**: Specific error handling for geocoding failures
  - Returns HTTP 400 (Bad Request) for geocoding errors
  - Returns HTTP 500 (Server Error) for other errors
  - Provides clear error messages to users

---

## ✅ What's Considered "Real" Coordinates

### Real Coordinates (Allowed):
1. **City Lookup Table**: Coordinates from the 50+ city lookup table
   - These are actual city center coordinates
   - Example: San Francisco, CA → 37.7749°N, -122.4194°W

2. **Google Maps API**: Valid coordinates from Google Geocoding API
   - Must pass validation checks
   - Must be within valid range

3. **Nominatim API**: Valid coordinates from OpenStreetMap Nominatim
   - Must pass validation checks
   - Must be within valid range

### Synthetic Defaults (Now Raises Error):
1. **Chicago Default for Non-Chicago Addresses**: 
   - If address is "123 Main St, San Francisco, CA" but geocoding returns Chicago coordinates
   - This will raise `GeocodingError`

2. **Invalid Coordinates**: 
   - (0,0) coordinates
   - Coordinates outside valid range
   - Invalid US coordinates (positive longitude for US addresses)

---

## 🎯 Validation Rules

### Coordinate Validation:
1. **Latitude**: Must be between -90 and 90
2. **Longitude**: Must be between -180 and 180
3. **Not (0,0)**: Cannot be exactly at origin
4. **US Address Validation**: 
   - US addresses must have negative longitude (west of prime meridian)
   - Latitude should be reasonable (20-55 for continental US, but allows Alaska/Hawaii)

### Chicago Default Detection:
- If coordinates match Chicago (41.8781, -87.6298) within 0.0001 tolerance
- AND address does NOT contain "chicago" or "il"
- THEN raise `GeocodingError`

---

## 📝 Example Error Messages

### Empty Address:
```
GeocodingError: Empty address provided. Please provide a valid address with city and state information.
```

### Geocoding Failed:
```
GeocodingError: Failed to geocode address 'Invalid Address XYZ'. Could not find real coordinates from any source (lookup table, Google Maps API, or Nominatim). Please provide a valid address with city and state information.
```

### Invalid Coordinates:
```
GeocodingError: Geocoding API returned invalid coordinates (0,0) for address '123 Main St'. This is not a real location.
```

### Chicago Default Detected:
```
GeocodingError: Geocoding returned Chicago default coordinates for non-Chicago address '123 Main St, San Francisco, CA'. This indicates geocoding failed. Please provide a valid address.
```

---

## 🧪 Testing

### Test Cases:
1. ✅ Valid address with city in lookup table → Should succeed
2. ✅ Valid address geocoded by API → Should succeed
3. ❌ Invalid address → Should raise `GeocodingError`
4. ❌ Empty address → Should raise `GeocodingError`
5. ❌ Address that geocodes to (0,0) → Should raise `GeocodingError`
6. ❌ Non-Chicago address that returns Chicago coordinates → Should raise `GeocodingError`

---

## ✅ Summary

**Before**: System would silently use Chicago coordinates as fallback, potentially causing incorrect simulations.

**After**: System raises `GeocodingError` if real coordinates cannot be found, ensuring all IDF files use actual location data.

This ensures that:
- ✅ All geocoded addresses use real coordinates
- ✅ No synthetic defaults are used
- ✅ Users get clear error messages when geocoding fails
- ✅ IDF files are always generated with accurate location data

