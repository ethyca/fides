# Demo Environment Setup Notes

This document contains configuration needed for local development and demo environments.

## Adobe Experience Platform Integration

### Environment Variable

**Location:** `/clients/privacy-center/.env`

**Variable:**
```bash
FIDES_PRIVACY_CENTER__ADOBE_ORG_ID=F207D74D549850760A4C98C6@AdobeOrg
```

### What It Does

This sets the Adobe Marketing Cloud Organization ID globally as `window.adobe_mc_orgid` before Adobe scripts load. This is required by:
- Adobe Visitor API (ECID)
- Adobe Experience Platform Web SDK
- Adobe Analytics (AppMeasurement)

### How It Works

1. Privacy Center reads `FIDES_PRIVACY_CENTER__ADOBE_ORG_ID` from `.env`
2. Injects it into the `/api/fides.js` bundle as:
   ```javascript
   window.adobe_mc_orgid = "F207D74D549850760A4C98C6@AdobeOrg";
   ```
3. Adobe scripts use this global variable for initialization

### Load Order (Critical)

Ensure Fides.js loads **before** Adobe Launch on your page:

```html
✅ CORRECT:
<script src="https://your-privacy-center/api/fides.js"></script>
<script src="https://assets.adobedtm.com/.../launch-xyz.min.js"></script>

❌ WRONG:
<script src="https://assets.adobedtm.com/.../launch-xyz.min.js"></script>
<script src="https://your-privacy-center/api/fides.js"></script>
```

### Testing

After restarting Privacy Center, verify in browser console:
```javascript
// Should show the Org ID
console.log(window.adobe_mc_orgid);

// Should return diagnostics including ECID
const aep = window.Fides.aep();
const diagnostics = aep.dump();
console.log(diagnostics.visitor.marketingCloudVisitorID);
```

## Other Configuration

### Google Tag Manager (Optional)

**Location:** `/clients/sample-app/.env` (sample app only)

**Variable:**
```bash
FIDES_SAMPLE_APP__GOOGLE_TAG_MANAGER_CONTAINER_ID=GTM-ABCD123
```

Note: This is only for the sample app demo. Real customers don't need an env var - they just call `Fides.gtm()` and configure in their GTM container.

## Restart Requirements

After changing `.env` files:
- **Privacy Center**: Restart `npm run dev` in `/clients/privacy-center`
- **Sample App**: Restart `npm run dev` in `/clients/sample-app`
- **Browser**: Hard refresh (Cmd+Shift+R / Ctrl+Shift+R) to clear cached bundles
