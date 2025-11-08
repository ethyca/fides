# Testing Adobe Consent Integration

Quick guide to verify that Fides consent changes are syncing to Adobe.

## Setup

1. Ensure Privacy Center is running with Adobe Org ID configured:
```bash
# In /clients/privacy-center/.env
FIDES_PRIVACY_CENTER__ADOBE_ORG_ID=F207D74D549850760A4C98C6@AdobeOrg
```

2. Load your page with:
```html
<script src="/api/fides.js"></script>
<script>Fides.aep({ debug: true })</script>
<script src="https://assets.adobedtm.com/.../launch.min.js"></script>
```

## Testing Consent Flow

### 1. Initialize Integration

```javascript
// Initialize with debug mode
const aep = window.Fides.aep({ debug: true });
```

### 2. Check Initial State (Before User Action)

```javascript
// Get current Adobe consent state
const initialState = aep.consent();
console.log('Initial Adobe Consent:', initialState);

// Example output:
// {
//   timestamp: "2025-11-08T...",
//   alloy: { configured: true },
//   ecidOptIn: {
//     configured: true,
//     aa: false,        // Analytics - denied
//     target: false,    // Target - denied
//     aam: false        // Audience Manager - denied
//   },
//   summary: {
//     analytics: false,
//     personalization: false,
//     advertising: false
//   }
// }
```

### 3. User Accepts Consent

Open Fides modal and click "Accept All" (or customize preferences).

### 4. Check Updated State

```javascript
// Wait a moment for consent to sync, then check again
setTimeout(() => {
  const updatedState = aep.consent();
  console.log('Updated Adobe Consent:', updatedState);

  // Should show approved consents:
  // {
  //   ecidOptIn: {
  //     aa: true,        // Analytics - APPROVED ✅
  //     target: true,    // Target - APPROVED ✅
  //     aam: true        // Audience Manager - APPROVED ✅
  //   },
  //   summary: {
  //     analytics: true,
  //     personalization: true,
  //     advertising: true
  //   }
  // }
}, 1000);
```

### 5. Verify Consent Changed

```javascript
// Compare before and after
console.log('Analytics consent changed:',
  initialState.summary.analytics !== updatedState.summary.analytics
);
```

## Quick Test Function

Copy and paste this into your browser console:

```javascript
// Get AEP integration
const aep = window.Fides.aep({ debug: true });

// Test function
async function testAdobeConsent() {
  console.log('=== Adobe Consent Test ===');

  // Check initial state
  const before = aep.consent();
  console.log('Before:', before.summary);

  // Wait for user to change consent in modal...
  console.log('👉 Now change your consent preferences in the Fides modal...');
  console.log('Run testAdobeConsent() again to see the difference.');

  // Or check after a delay
  setTimeout(() => {
    const after = aep.consent();
    console.log('After:', after.summary);

    // Show what changed
    const changes = {
      analytics: before.summary.analytics !== after.summary.analytics,
      personalization: before.summary.personalization !== after.summary.personalization,
      advertising: before.summary.advertising !== after.summary.advertising,
    };
    console.log('Changed:', changes);
  }, 2000);
}

// Run it
testAdobeConsent();
```

## Expected Results

### Scenario 1: Accept All
```javascript
aep.consent().summary
// ✅ { analytics: true, personalization: true, advertising: true }
```

### Scenario 2: Reject All
```javascript
aep.consent().summary
// ✅ { analytics: false, personalization: false, advertising: false }
```

### Scenario 3: Custom (Analytics Only)
```javascript
aep.consent().summary
// ✅ { analytics: true, personalization: false, advertising: false }
```

## Troubleshooting

### No consent data showing?

```javascript
// Check if Adobe is loaded
const diagnostics = aep.dump();
console.log('Adobe configured:', {
  alloy: diagnostics.alloy?.configured,
  visitor: diagnostics.visitor?.configured,
  optIn: diagnostics.optIn?.configured,
});

// Check ECID
console.log('ECID:', diagnostics.visitor?.marketingCloudVisitorID);
```

### Consent not changing?

```javascript
// Verify Fides events are firing
window.addEventListener('FidesUpdated', (evt) => {
  console.log('Fides consent changed:', evt.detail.consent);
  console.log('Adobe consent now:', aep.consent().summary);
});
```

### Debug mode not working?

```javascript
// Re-initialize with debug
const aep = window.Fides.aep({ debug: true });

// You should see console logs like:
// [Fides Adobe] Pushing consent to Adobe: { analytics: true, ... }
// [Fides Adobe] Sent consent to Adobe Web SDK
```

## Console Log Verification

With `debug: true`, you should see:

```
[Fides Adobe] Pushing consent to Adobe: { analytics: true, functional: false, ... }
[Fides Adobe] Sent consent to Adobe Web SDK: { purposes: { collect: 'in', ... } }
[Fides Adobe] Updated ECID Opt-In Service
```

## Adobe Experience Platform Debugger

Install the Chrome extension: [Adobe Experience Platform Debugger](https://chrome.google.com/webstore/detail/adobe-experience-platform/bfnnokhpnncpkdmbokanobigaccjkpob)

**Verify:**
1. Open the debugger
2. Go to "Consent" tab
3. Check consent status matches `aep.consent().summary`
4. Verify Analytics beacons fire (or don't) based on consent

## Common Issues

| Issue | Solution |
|-------|----------|
| `aep.consent()` returns all false | Adobe Opt-In not initialized yet. Wait a moment after page load. |
| Consent doesn't change after accepting | Check console for errors. Ensure Adobe scripts loaded before Fides. |
| No ECID | Check `window.adobe_mc_orgid` is set. Should be your Org ID. |
| Debug logs not showing | Re-initialize: `Fides.aep({ debug: true })` |

## Success Criteria

✅ Initial page load: `aep.consent().ecidOptIn.configured === true`
✅ ECID present: `aep.dump().visitor.marketingCloudVisitorID !== undefined`
✅ Accept All: All `aep.consent().summary` values become `true`
✅ Reject All: All `aep.consent().summary` values become `false`
✅ Debug logs: See "[Fides Adobe]" messages in console
✅ Adobe Debugger: Consent status matches Fides consent
