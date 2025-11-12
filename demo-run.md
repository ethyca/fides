# Manual Demo Run Guide: Fides ↔ Adobe ↔ OneTrust Integration

This guide demonstrates a **realistic migration scenario** on nvidia.com, showing:
1. Current state (OneTrust + Adobe)
2. User interaction with OneTrust
3. Fides injection and migration
4. User interaction with Fides

All verifications use Adobe's native debugging tools and one-liner console checks.

---

## Step 1: Setup - Open Tools and Load Page

### 1.1 Open Browser Tools

1. **Open Adobe Experience Cloud Debugger**
   - Click the extension icon in your browser
   - Pin it for easy access

2. **Open Chrome DevTools**
   - Press `F12` or `Cmd+Option+I` (Mac) / `Ctrl+Shift+I` (Windows)
   - Go to the **Console** tab

### 1.2 Load nvidia.com

Navigate to: **https://nvidia.com**

**DO NOT accept or interact with the OneTrust banner yet.**

---

## Step 2: Pre-Migration State (Before Fides)

This simulates the current production state with OneTrust + Adobe.

### 2.1 Initial Pre-Check (Before User Interaction)

Run these one-liners in the console to check the current state:

```javascript
// Check OneTrust
document.cookie.match(/OptanonConsent=([^;]+)/)?.[1]?.match(/groups=([^&]+)/)?.[1] || 'Not set'

// Check Adobe ECID Opt-In
(() => { const o = window.adobe?.optIn; return o ? { aa: o.isApproved(o.Categories.ANALYTICS), target: o.isApproved(o.Categories.TARGET), aam: o.isApproved(o.Categories.AAM) } : 'Not loaded'; })()

// Check Google gtag consent (last consent command)
window.dataLayer?.filter(i => i[0] === 'consent').pop() || 'No gtag'
```

**Expected Results:**
- **OneTrust:** Shows active groups (e.g., `C0001%2CC0002`) or 'Not set'
- **Adobe ECID:** May show all `false` or `undefined` (pending user choice)
- **Google gtag:** Shows last consent state or 'No gtag'

**Adobe Debugger Check:**
- **Summary** tab: Should show Adobe products loaded (ECID, Analytics, Launch, etc.)
- **ECID** tab: Shows visitor ID, Opt-In Service may show "Pending" or categories denied
- **Consent** tab: May show no consent or default deny state

---

### 2.2 User Accepts OneTrust Consent

**Interact with the OneTrust banner:**
1. Click "Cookie Settings" or "Manage Preferences"
2. Toggle ON: **Performance Cookies** and **Functional Cookies**
3. Leave OFF: **Advertising Cookies**
4. Click "Confirm My Choices"

**The page will likely reload.** Wait for it to reload, then continue.

---

### 2.3 Post-Interaction Pre-Check

After the page reloads, run the same one-liners to see what changed:

```javascript
// Check OneTrust - should show accepted groups
document.cookie.match(/OptanonConsent=([^;]+)/)?.[1]?.match(/groups=([^&]+)/)?.[1] || 'Not set'

// Check Adobe ECID Opt-In - should show approvals
(() => { const o = window.adobe?.optIn; return o ? { aa: o.isApproved(o.Categories.ANALYTICS), target: o.isApproved(o.Categories.TARGET), aam: o.isApproved(o.Categories.AAM) } : 'Not loaded'; })()

// Check Google gtag consent
window.dataLayer?.filter(i => i[0] === 'consent').pop() || 'No gtag'
```

**Expected Results:**
- **OneTrust:** Shows `C0001%2CC0002%2CC0003` (Essential + Performance + Functional)
- **Adobe ECID:** `{ aa: true, target: true, aam: false }`
- **Google gtag:** Should show granted for analytics_storage, functionality_storage, personalization_storage

**Adobe Debugger Check:**
- **ECID** tab:
  - Analytics (AA): ✅ Approved
  - Target: ✅ Approved
  - AAM: ❌ Denied
- **Consent** tab: Web SDK purposes show "in" for collect, measure, personalize

**Key Observation:** OneTrust → Adobe ECID sync is working natively.

---

## Step 3: Migration - Inject Fides and Replace OneTrust

Now we simulate the "migration day" where Fides replaces OneTrust.

### 3.1 Run the Migration Script

**Copy and paste this entire script into the console:**

```javascript
(async () => {
  console.log('🚀 Starting Fides migration...\n');

  // Step 1: Inject Fides.js
  console.log('Step 1: Injecting Fides.js...');
  await fetch('https://braverobot.net/fides.js?geolocation=us-ca&property_id=FDS-228IX4')
    .then(r => r.text())
    .then(t => {
      const s = document.createElement('script');
      s.textContent = t;
      document.head.appendChild(s);
    });

  // Wait for Fides to initialize
  await new Promise(resolve => setTimeout(resolve, 500));

  if (!window.Fides) {
    console.error('❌ Fides failed to load');
    return;
  }
  console.log('✅ Fides loaded');

  // Step 2: Read OneTrust consent and initialize Fides
  console.log('\nStep 2: Reading OneTrust consent...');
  const otCookie = document.cookie.match(/OptanonConsent=([^;]+)/)?.[1];
  if (!otCookie) {
    console.error('❌ OneTrust cookie not found');
    return;
  }

  // Parse OneTrust groups
  const groups = otCookie.match(/groups=([^&]+)/)?.[1]?.split('%2C') || [];
  const otConsent = {
    essential: groups.includes('C0001'),
    performance: groups.includes('C0002'),
    functional: groups.includes('C0003'),
    advertising: groups.includes('C0004')
  };

  console.log('✅ OneTrust consent:', otConsent);

  // Initialize Fides from OneTrust
  window.Fides.consent = otConsent;
  console.log('✅ Fides consent initialized');

  // Step 3: Setup Adobe integration
  console.log('\nStep 3: Setting up Adobe integration...');
  window.fidesAEP = Fides.aep({
    purposeMapping: {
      performance: ['collect', 'measure'],
      functional: ['personalize'],
      advertising: ['personalize', 'share']
    },
    ecidMapping: {
      performance: ['aa'],
      functional: ['target'],
      advertising: ['aam']
    },
    debug: true
  });
  console.log('✅ Adobe integration active');

  // Step 4: Setup Google Consent Mode integration
  console.log('\nStep 4: Setting up Google Consent Mode...');
  window.fidesGtag = Fides.gtagConsent({
    purposeMapping: {
      performance: ['analytics_storage'],
      functional: ['functionality_storage', 'personalization_storage'],
      advertising: ['ad_storage', 'ad_personalization', 'ad_user_data']
    },
    debug: true
  });
  console.log('✅ Google Consent Mode active');

  // Dispatch initial update to sync everything
  window.dispatchEvent(new CustomEvent('FidesUpdated', {
    detail: {
      consent: window.Fides.consent,
      extraDetails: { trigger: { origin: 'migration_init' } }
    }
  }));

  console.log('\n✅ Migration complete! Fides is now controlling consent.\n');

  // Step 5: Show Fides modal
  console.log('Step 5: Opening Fides consent modal...');
  await new Promise(resolve => setTimeout(resolve, 500));
  Fides.showModal();

  console.log('\n📊 Integration status saved to: window.fidesAEP and window.fidesGtag');
  console.log('🔍 Check consent anytime with: window.Fides.consent');
})();
```

**Wait for the script to complete.** You should see:
- ✅ Messages confirming each step
- The Fides consent modal appears
- Console logs from Adobe integration showing sync activity

### 3.2 Verify Migration Success

Run the one-liners again to confirm state was preserved:

```javascript
// Check Fides consent
window.Fides.consent

// Check Adobe ECID Opt-In - should match pre-migration state
(() => { const o = window.adobe?.optIn; return o ? { aa: o.isApproved(o.Categories.ANALYTICS), target: o.isApproved(o.Categories.TARGET), aam: o.isApproved(o.Categories.AAM) } : 'Not loaded'; })()

// Check Google gtag consent - should match pre-migration state
window.dataLayer?.filter(i => i[0] === 'consent').pop()
```

**Expected Results:**
- **Fides consent:** Matches what OneTrust had (from Step 2.3)
- **Adobe ECID:** Same as Step 2.3 - `{ aa: true, target: true, aam: false }`
- **Google gtag:** Same as Step 2.3 - analytics_storage/functionality_storage granted

**Adobe Debugger Check:**
- **ECID** tab: Approvals should be **identical** to Step 2.3
- No change in consent state (seamless migration)

**Key Observation:** Fides read OneTrust state and synced it to Adobe without any user-facing changes.

---

## Step 4: Post-Migration - User Interactions with Fides

Now the user interacts with the Fides modal (which should be open from Step 3).

### 4.1 User Toggles Advertising ON

**In the Fides modal:**
1. Find the **Advertising** toggle
2. Toggle it **ON**
3. Click **Save**

The modal should close.

### 4.2 Check Consent State (Immediately After)

Run the check one-liners to see what changed:

```javascript
// Check Fides consent - advertising should now be true
window.Fides.consent

// Check Adobe ECID Opt-In - AAM should now be approved
(() => { const o = window.adobe?.optIn; return o ? { aa: o.isApproved(o.Categories.ANALYTICS), target: o.isApproved(o.Categories.TARGET), aam: o.isApproved(o.Categories.AAM) } : 'Not loaded'; })()

// Check Google gtag - ad_storage should be granted
window.dataLayer?.filter(i => i[0] === 'consent').slice(-2)
```

**Expected Results:**
- **Fides consent:** `{ essential: true, performance: true, functional: true, advertising: true }`
- **Adobe ECID:** `{ aa: true, target: true, aam: true }` ← AAM now approved!
- **Google gtag:** Last consent command shows `ad_storage: 'granted'`, `ad_personalization: 'granted'`

**Adobe Debugger Check:**
- Refresh the **ECID** tab
- **AAM:** Should now show ✅ Approved

**Console Logs:**
Look for:
```
[Fides Adobe] Pushing consent to Adobe: {advertising: true, ...}
[Fides Adobe] ECID approvals computed from ecidMapping: {aa: true, target: true, aam: true}
[Fides Adobe] Updated ECID Opt-In Service: {aa: true, target: true, aam: true}
[Fides gtag] Consent update: {ad_storage: 'granted', ad_personalization: 'granted', ad_user_data: 'granted'}
```

---

### 4.3 User Opts Out of Performance

**Re-open the Fides modal:**
```javascript
Fides.showModal();
```

**In the modal:**
1. Toggle **Performance** OFF
2. Click **Save**

### 4.4 Check Consent State

```javascript
// Check Fides consent - performance should now be false
window.Fides.consent

// Check Adobe ECID Opt-In - AA should now be denied
(() => { const o = window.adobe?.optIn; return o ? { aa: o.isApproved(o.Categories.ANALYTICS), target: o.isApproved(o.Categories.TARGET), aam: o.isApproved(o.Categories.AAM) } : 'Not loaded'; })()

// Check Google gtag
window.dataLayer?.filter(i => i[0] === 'consent').slice(-2)
```

**Expected Results:**
- **Fides consent:** `{ essential: true, performance: false, functional: true, advertising: true }`
- **Adobe ECID:** `{ aa: false, target: true, aam: true }` ← Analytics now denied!
- **Google gtag:** `analytics_storage: 'denied'`

**Adobe Debugger Check:**
- Refresh **ECID** tab
- **Analytics (AA):** Should now show ❌ Denied

---

### 4.5 User Opts Out of Everything (Except Essential)

**Re-open modal and toggle everything OFF (except Essential cannot be toggled):**

```javascript
Fides.showModal();
// Toggle all OFF, then Save
```

### 4.6 Final Check

```javascript
// Check Fides consent - only essential should be true
window.Fides.consent

// Check Adobe ECID Opt-In - all should be denied
(() => { const o = window.adobe?.optIn; return o ? { aa: o.isApproved(o.Categories.ANALYTICS), target: o.isApproved(o.Categories.TARGET), aam: o.isApproved(o.Categories.AAM) } : 'Not loaded'; })()

// Check Google gtag
window.dataLayer?.filter(i => i[0] === 'consent').slice(-2)
```

**Expected Results:**
- **Fides consent:** `{ essential: true, performance: false, functional: false, advertising: false }`
- **Adobe ECID:** `{ aa: false, target: false, aam: false }` ← All denied!
- **Google gtag:** All types `'denied'`

**Adobe Debugger Check:**
- **ECID** tab: All categories ❌ Denied

---

## Step 5: Advanced Verification

### 5.1 Comprehensive Diagnostic Dump

Get full diagnostics across all systems:

```javascript
// NVIDIA-specific status (shows everything)
const diagnostics = Fides.nvidia.status();
console.log(diagnostics);

// Consent state with mapping chain
const consentState = Fides.nvidia.consent();
console.table(consentState.rows);
```

### 5.2 Check OneTrust Cookie Sync

Verify Fides is writing back to OneTrust cookie:

```javascript
// Parse OneTrust cookie to see if Fides updated it
const otCookie = document.cookie.match(/OptanonConsent=([^;]+)/)?.[1];
const groups = otCookie?.match(/groups=([^&]+)/)?.[1]?.split('%2C') || [];
console.log('OneTrust groups:', groups);
console.log('Expected based on Fides:', {
  C0001: window.Fides.consent.essential,
  C0002: window.Fides.consent.performance,
  C0003: window.Fides.consent.functional,
  C0004: window.Fides.consent.advertising
});
```

**Expected:** OneTrust cookie groups should match Fides consent state

### 5.3 Verify ECID Persistence

Check that ECID didn't change during migration:

```javascript
// Get current ECID
const visitor = window.Visitor?.getInstance(window.adobe_mc_orgid);
const currentECID = visitor?.getMarketingCloudVisitorID();
console.log('Current ECID:', currentECID);

// Should be the same ECID from Step 2
// Verify by checking Adobe Debugger > ECID tab
```

**Key Observation:** ECID should remain the same - user identity preserved across migration

---

## Success Criteria

✅ **Pre-migration state captured** - OneTrust + Adobe working before Fides

✅ **Seamless migration** - Fides initialized from OneTrust without breaking consent

✅ **Real-time sync** - Fides → Adobe ECID updates immediately

✅ **Real-time sync** - Fides → Google gtag updates immediately

✅ **Bidirectional sync** - OneTrust cookie reflects Fides changes

✅ **User identity preserved** - ECID remains constant

✅ **Independent mappings work** - Web SDK and ECID can be configured separately

✅ **Debug mode provides visibility** - All integration activity visible in console

---

## Quick Reference: One-Liner Checks

Save these for easy copy-paste during demos:

```javascript
// Fides consent
window.Fides.consent

// Adobe ECID Opt-In status
(() => { const o = window.adobe?.optIn; return o ? { aa: o.isApproved(o.Categories.ANALYTICS), target: o.isApproved(o.Categories.TARGET), aam: o.isApproved(o.Categories.AAM) } : 'Not loaded'; })()

// Google gtag last consent command
window.dataLayer?.filter(i => i[0] === 'consent').pop()

// OneTrust active groups
document.cookie.match(/OptanonConsent=([^;]+)/)?.[1]?.match(/groups=([^&]+)/)?.[1] || 'Not set'

// ECID value
window.Visitor?.getInstance(window.adobe_mc_orgid)?.getMarketingCloudVisitorID()

// Open Fides modal
Fides.showModal()

// Full diagnostics
Fides.nvidia.status()

// Consent mapping table
console.table(Fides.nvidia.consent().rows)
```

---

## Troubleshooting

### Issue: Migration script fails to load Fides

**Check:**
```javascript
// Verify fetch succeeded
typeof window.Fides === 'object'  // Should be true

// If failed, check URL
// Try loading directly in browser: https://braverobot.net/fides.js?geolocation=us-ca&property_id=FDS-228IX4
```

**Fix:** Check network tab in DevTools for any errors loading the script.

### Issue: Adobe ECID not updating after Fides changes

**Check:**
```javascript
// Verify Adobe optIn exists
window.adobe?.optIn

// Check if event listener is registered
window.addEventListener('FidesUpdated', (e) => console.log('Event fired:', e.detail));

// Then trigger an update
window.Fides.consent.performance = true;
window.dispatchEvent(new CustomEvent('FidesUpdated', { detail: { consent: window.Fides.consent } }));
```

**Fix:** Re-run the migration script (Step 3) to reinitialize integrations.

### Issue: OneTrust cookie doesn't reflect Fides changes

**Check:**
```javascript
// Check before
document.cookie.match(/OptanonConsent=([^;]+)/)?.[1]?.match(/groups=([^&]+)/)?.[1]

// Make a change
window.Fides.consent.advertising = true;
window.dispatchEvent(new CustomEvent('FidesUpdated', { detail: { consent: window.Fides.consent } }));

// Wait 1 second, then check again
setTimeout(() => {
  console.log(document.cookie.match(/OptanonConsent=([^;]+)/)?.[1]?.match(/groups=([^&]+)/)?.[1]);
}, 1000);
```

**Note:** Cookie writes are asynchronous. Allow ~500ms for the write to complete.

### Issue: Fides modal doesn't appear

**Check:**
```javascript
// Verify Fides is loaded
typeof window.Fides.showModal === 'function'

// Try showing it manually
Fides.showModal();
```

**Fix:** Check console for errors. Modal may require certain DOM elements to exist.

### Issue: Adobe Debugger shows stale data

**Fix:** Click the refresh button in each tab of the Adobe Debugger extension. Some tabs don't auto-update.

### Issue: Google gtag consent not updating

**Check:**
```javascript
// Verify gtag exists
typeof window.gtag === 'function'

// Check dataLayer
window.dataLayer
```

**Note:** If `window.gtag` doesn't exist, the Google integration will silently skip (not an error). NVIDIA.com may or may not have gtag depending on the page.
