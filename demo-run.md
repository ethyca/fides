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
  // Inject Fides
  await fetch('https://braverobot.net/fides.js?geolocation=us-ca&property_id=FDS-228IX4')
    .then(r => r.text())
    .then(t => {
      const s = document.createElement('script');
      s.textContent = t;
      document.head.appendChild(s);
    });

  await new Promise(resolve => setTimeout(resolve, 500));

  // Migrate from OneTrust
  Fides.onetrust.migrate();

  // Setup Adobe integration
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

  // Setup Google Consent Mode
  window.fidesGtag = Fides.gtagConsent({
    purposeMapping: {
      performance: ['analytics_storage'],
      functional: ['functionality_storage', 'personalization_storage'],
      advertising: ['ad_storage', 'ad_personalization', 'ad_user_data']
    },
    debug: true
  });

  // Show modal
  await new Promise(resolve => setTimeout(resolve, 500));
  Fides.showModal();
})();
```

The modal will open automatically. Watch the console for `[Fides Adobe]` and `[Fides gtag]` debug logs.

### 3.2 Verify Migration Success

Run the one-liners to confirm state was preserved:

```javascript
// Fides consent
window.Fides.consent

// Adobe ECID
(() => { const o = window.adobe?.optIn; return o ? { aa: o.isApproved(o.Categories.ANALYTICS), target: o.isApproved(o.Categories.TARGET), aam: o.isApproved(o.Categories.AAM) } : 'Not loaded'; })()

// Google gtag
window.dataLayer?.filter(i => i[0] === 'consent').pop()
```

Should match Step 2.3 state. Check Adobe Debugger ECID tab - approvals should be identical.

---

## Step 4: Post-Migration - User Interactions with Fides

The Fides modal is open. Interact with it and verify sync.

### 4.1 Toggle Advertising ON

In the modal: Toggle **Advertising** ON → Click **Save**

Check state:

```javascript
window.Fides.consent
(() => { const o = window.adobe?.optIn; return o ? { aa: o.isApproved(o.Categories.ANALYTICS), target: o.isApproved(o.Categories.TARGET), aam: o.isApproved(o.Categories.AAM) } : 'Not loaded'; })()
window.dataLayer?.filter(i => i[0] === 'consent').slice(-2)
```

Adobe ECID AAM should now be approved. Check Adobe Debugger ECID tab.

---

### 4.2 Toggle Performance OFF

Re-open modal:

```javascript
Fides.showModal();
```

In modal: Toggle **Performance** OFF → Click **Save**

Check state (same one-liners). Adobe ECID AA should now be denied.

---

### 4.3 Opt Out of Everything

Re-open modal, toggle all OFF (except Essential), Save.

Check state (same one-liners). All Adobe ECID categories should be denied.

---

## Step 5: Advanced Verification

Get full diagnostics:

```javascript
Fides.nvidia.status()
console.table(Fides.nvidia.consent().rows)
```

Verify ECID didn't change:

```javascript
window.Visitor?.getInstance(window.adobe_mc_orgid)?.getMarketingCloudVisitorID()
```

Should be same as Step 2.

---

## Success Criteria

- Pre-migration state captured (OneTrust + Adobe)
- Seamless migration (Fides reads OneTrust without breaking consent)
- Real-time sync (Fides → Adobe ECID, Fides → Google gtag)
- ECID preserved (same visitor ID before/after)
- Independent mappings (Web SDK vs ECID configured separately)

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

**Fides didn't load:** Check network tab for errors, verify URL is accessible

**Adobe ECID not updating:** Re-run migration script, check `window.adobe?.optIn` exists

**Modal doesn't appear:** `Fides.showModal()` - check console for errors

**Adobe Debugger stale:** Click refresh button in each tab

**gtag not found:** NVIDIA may not have gtag on all pages (not an error)
