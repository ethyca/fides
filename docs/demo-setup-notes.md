# Adobe Integration Demo Guide

This document shows how to demo the Fides ↔ Adobe ↔ OneTrust integration.

## Quick Demo on nvidia.com

The easiest way to demo the Adobe integration is using **nvidia.com** (which has both OneTrust and Adobe ECID installed):

### 1. Inject Your Dev Fides.js

Use this bookmarklet to inject your local dev environment onto nvidia.com:

```javascript
javascript:(function(){fetch('https://fides-js.ngrok.dev/fides.js').then(r=>r.text()).then(t=>{const s=document.createElement('script');s.textContent=t;document.head.appendChild(s);setTimeout(()=>{console.log('Fides loaded:',!!window.Fides);},500);});})();
```

**Note**: Replace `fides-js.ngrok.dev` with your actual ngrok/tunnel URL.

Wait 2-3 seconds for Fides to load, then verify:

```javascript
console.log(window.Fides); // Should show Fides object
```

### 2. Run the Demo

```javascript
const aep = await Fides.nvidiaDemo();

// Demo automatically:
// ✅ Detects OneTrust categories (C0001-C0004)
// ✅ Suggests Fides notice mappings
// ✅ Initializes Fides from OneTrust
// ✅ Creates Adobe integration with correct purpose mapping
// ✅ Demonstrates consent sync across all systems
// ✅ Tests: Toggle notice, Opt-in all, Opt-out all
// ✅ Returns the live aep integration instance
```

### 3. Continue Testing

The demo returns the live `aep` instance, so you can continue testing:

```javascript
// Check current consent state
aep.consent();
// { alloy: {...}, ecidOptIn: {...}, summary: {...} }

// Manually update Fides consent
window.Fides.consent.performance = true;
window.dispatchEvent(new CustomEvent('FidesUpdated', {
  detail: { consent: window.Fides.consent }
}));

// Wait 500ms, then check Adobe again
setTimeout(() => {
  console.log(aep.consent());
  // Adobe should reflect the change!
}, 500);

// Check what OneTrust has
aep.oneTrust.read();
// { essential: true, performance: true, ... }

// Get full diagnostics
aep.dump();
```

### 4. How It Works

After `nvidiaDemo()` runs:

1. **Adobe integration is LIVE** - `aep` instance is subscribed to `FidesUpdated` events
2. **Any changes to `window.Fides.consent`** will automatically:
   - Update Adobe Web SDK (via `setConsent()`)
   - Update Adobe ECID Opt-In (via `approve()`/`deny()`)
   - Update OneTrust cookie (via cookie write)
3. **Sync happens on EVERY update** - No need to re-initialize

```javascript
// This pattern works indefinitely after demo:
window.Fides.consent.advertising = false;
window.dispatchEvent(new CustomEvent('FidesUpdated', {
  detail: { consent: window.Fides.consent }
}));
// → Adobe ECID opt-out of 'aam' (Audience Manager)
// → OneTrust cookie updated
```

## Manual Setup (Without Demo)

If you want to test without the demo or on a different site:

### Step 1: Initialize Adobe Integration

```javascript
// Auto-detect from OneTrust (requires OneTrust present)
const aep = Fides.aep();
const suggestion = aep.suggest();
if (suggestion.success) {
  // Re-initialize with suggested mapping
  const aep = Fides.aep({
    purposeMapping: suggestion.purposeMapping
  });
}

// OR: Manual purpose mapping
const aep = Fides.aep({
  purposeMapping: {
    analytics: ['collect', 'measure'],      // Adobe Analytics (aa)
    functional: ['personalize'],            // Adobe Target (target)
    advertising: ['personalize', 'share']   // Adobe AAM (aam)
  },
  debug: true
});
```

### Step 2: Check Diagnostics

```javascript
aep.dump();
// Shows: Fides, Adobe Web SDK, ECID, OneTrust status

aep.consent();
// Shows: Current Adobe consent state

aep.oneTrust.read();
// Shows: Current OneTrust consent
```

### Step 3: Test Updates

```javascript
// Update a single notice
window.Fides.consent.performance = true;
window.dispatchEvent(new CustomEvent('FidesUpdated', {
  detail: { consent: window.Fides.consent }
}));

// Check results
setTimeout(() => console.log(aep.consent()), 500);
```

## Environment Configuration

### Adobe Marketing Cloud Org ID

**Location:** `/clients/privacy-center/.env`

```bash
FIDES_PRIVACY_CENTER__ADOBE_ORG_ID=F207D74D549850760A4C98C6@AdobeOrg
```

This is injected as `window.adobe_mc_orgid` before Adobe scripts load.

**Restart Required:** Privacy Center dev server after changing `.env`

### Verification

```javascript
// Should show the Org ID
console.log(window.adobe_mc_orgid);
// "F207D74D549850760A4C98C6@AdobeOrg"

// Should show ECID
const aep = Fides.aep();
console.log(aep.dump().visitor.marketingCloudVisitorID);
// "921765717357756231576074585251..."
```

## Troubleshooting

### Demo Fails: "OneTrust not detected"

- Make sure you're on a page with OneTrust (like nvidia.com)
- Check `document.cookie` includes `OptanonConsent`
- Try `aep.dump().oneTrust` to see what's detected

### Adobe Not Updating

- Check `aep.consent()` to see current Adobe state
- Verify purpose mapping matches your Fides consent keys
- Enable debug: `Fides.aep({ debug: true })`
- Check browser console for `[Fides Adobe]` logs

### OneTrust Not Syncing

- OneTrust SDK causes page reload if `UpdateConsent()` is used
- Currently using cookie write (works but OneTrust SDK may not reflect changes immediately)
- Check `aep.oneTrust.read()` to verify cookie was written

### Load Order Issues

Fides must load **before** Adobe Launch:

```html
✅ CORRECT:
<script src="fides.js"></script>
<script>Fides.aep();</script>
<script src="launch-xyz.min.js"></script>

❌ WRONG:
<script src="launch-xyz.min.js"></script>
<script src="fides.js"></script>
```

## Production Usage

In production, customers would:

1. **Configure in Admin UI** (when implemented):
   - Enable Adobe destination
   - Set Adobe Org ID
   - Map Fides notices → Adobe purposes

2. **Add to their site** (one line):
   ```html
   <script src="https://your-privacy-center/api/fides.js"></script>
   ```

3. **Fides automatically**:
   - Reads from OneTrust (if migrating)
   - Syncs consent to Adobe Web SDK & ECID
   - Updates on every consent change

No manual `aep()` calls needed - it's configured server-side!
