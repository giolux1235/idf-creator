# Railway EnergyPlus Service - Restart and Deployment Instructions

**Service URL**: `https://web-production-1d1be.up.railway.app/simulate`

---

## 🚀 **Quick Restart (If Auto-Deploy Enabled)**

If your Railway service is connected to this GitHub repository:

1. **Push latest code** (already done ✅)
   ```bash
   git push origin main
   ```

2. **Railway will automatically deploy** (usually 2-5 minutes)
   - Check Railway dashboard for deployment status
   - Wait for "Deployment Successful" message

3. **Test the service**:
   ```bash
   python restart_and_test_railway_service.py
   ```

---

## 🔧 **Manual Restart (Railway Dashboard)**

1. **Go to Railway Dashboard**:
   - https://railway.app
   - Navigate to your service: `web-production-1d1be`

2. **Restart Service**:
   - Click on your service
   - Go to "Settings" or "Deployments" tab
   - Click "Redeploy" or "Restart"

3. **Check Logs**:
   - Go to "Logs" tab
   - Verify service starts without errors
   - Look for: "🌐 Starting IDF Creator Web Interface..."

4. **Wait for deployment** (2-5 minutes)

---

## 📋 **Verify Code is Deployed**

The Railway service needs the SQLite extraction fixes. Check:

### Required Code in `web_interface.py`:

1. **SQLite extraction with MAX()** (lines 888-1126):
   - Should use `MAX(Value)` for RunPeriod meters
   - Should try multiple query strategies

2. **Extraction method tracking** (lines 880, 1122):
   - Should set `energy_results['extraction_method'] = 'sqlite'` or `'standard'`

3. **Better error logging** (line 1129):
   - Should log SQLite extraction errors

### Check if code is deployed:

```bash
# Test the service
python restart_and_test_railway_service.py

# If it returns extraction_method: 'sqlite', the fixes are deployed ✅
```

---

## 🔍 **Troubleshooting**

### Service Not Responding

**Symptoms**:
- SSL errors
- Connection timeouts
- 503/502 errors

**Solutions**:
1. **Wait 2-5 minutes** after code push (Railway needs time to deploy)
2. **Check Railway dashboard** for deployment status
3. **Check Railway logs** for errors
4. **Restart service manually** in Railway dashboard

### SQLite Extraction Not Working

**Symptoms**:
- `extraction_method: 'standard'` (not `'sqlite'`)
- Energy values 76% too low
- No `energy_results` in response

**Solutions**:
1. **Verify Output:SQLite in IDF files**:
   ```python
   # Check if IDF has Output:SQLite
   if 'Output:SQLite' in idf_content:
       print("✅ Output:SQLite found")
   ```

2. **Check Railway logs** for SQLite extraction errors:
   - Look for: "⚠️  SQLite extraction error:"
   - Verify SQLite file exists: `eplusout.sql`

3. **Verify SQLite extraction code**:
   - Should use `MAX(Value)` not `SUM(Value)`
   - Should have multiple query strategies

---

## ✅ **Verification Checklist**

After deployment, verify:

- [ ] Service is responding (no SSL/timeout errors)
- [ ] API returns `simulation_status: 'success'`
- [ ] API returns `energy_results` with values
- [ ] `extraction_method: 'sqlite'` (not `'standard'`)
- [ ] Energy values are reasonable (~100,000 kWh for medium office)
- [ ] EUI is 20-28 kWh/m² (not 5-8 kWh/m²)

---

## 📞 **If Service is Separate Repository**

If the Railway EnergyPlus service (`web-production-1d1be`) is in a **different repository**:

1. **Apply fixes** from `RAILWAY_ENERGYPLUS_SERVICE_DEPLOYMENT.md`
2. **Copy SQLite extraction code** from `web_interface.py` (lines 888-1126)
3. **Update extraction method tracking** (lines 880, 1122)
4. **Deploy to Railway**

---

## 🧪 **Test After Restart**

```bash
# Run test script
python restart_and_test_railway_service.py

# Or test with full workflow
python test_energy_extraction_fix.py
```

**Expected Results**:
- ✅ `extraction_method: 'sqlite'`
- ✅ `total_site_energy_kwh: ~100,000` (for medium office)
- ✅ `eui_kwh_m2: 20-28`

---

## 📊 **Monitoring**

**Check Railway Logs**:
1. Go to Railway dashboard
2. Select your service
3. Click "Logs" tab
4. Look for:
   - `✓ Extracted from SQLite: XXX.XX kWh` ✅
   - `⚠️  SQLite extraction error: ...` ❌

**Check API Response**:
```bash
curl -X POST https://web-production-1d1be.up.railway.app/simulate \
  -H "Content-Type: application/json" \
  -d '{"idf_content": "...", "idf_filename": "test.idf"}' \
  | jq '.energy_results.extraction_method'
```

Should return: `"sqlite"`

---

**Last Updated**: 2025-11-05  
**Status**: Ready for deployment

