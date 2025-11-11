# Adobe Experience Platform (AEP) Integration Configuration

This guide explains how to configure the Fides → Adobe integration.

## Quick Start

```javascript
// Basic setup with default mapping
Fides.aep();

// Custom mapping (if your Fides consent keys differ from defaults)
Fides.aep({
  purposeMapping: {
    analytics: ['collect', 'measure'],      // Adobe Analytics (aa)
    functional: ['personalize'],            // Adobe Target (target)
    advertising: ['personalize', 'share']   // Adobe AAM (aam)
  }
});
```

## Understanding Purpose Mapping

### Adobe Purposes

Adobe consent uses 4 purposes:
- **`collect`** - Collect data
- **`measure`** - Measure/analyze data (Analytics)
- **`personalize`** - Personalize content (Target)
- **`share`** - Share data with 3rd parties (Audience Manager)

### ECID Categories

For legacy ECID Opt-In Service, these map to:
- **`aa`** - Adobe Analytics → `collect`, `measure`
- **`target`** - Adobe Target → `personalize`
- **`aam`** - Adobe Audience Manager → `share`, `personalize`

### Default Mapping

If your Fides consent uses these keys, no configuration needed:
```javascript
{
  analytics: ['collect', 'measure'],      // → aa
  functional: ['personalize'],            // → target
  advertising: ['personalize', 'share']   // → aam
}
```

### Custom Mapping

If your Fides keys are different, provide a custom mapping:

```javascript
// Example: Your Fides uses different key names
Fides.aep({
  purposeMapping: {
    ai_analytics: ['collect', 'measure'],           // Your "ai_analytics" → Adobe Analytics
    marketing: ['personalize', 'share'],            // Your "marketing" → Target + AAM
    data_sales_and_sharing: ['share']               // Your key → AAM only
  }
});
```

## Migrating from OneTrust

### Standard OneTrust Categories

OneTrust typically uses:
- **C0001** - Strictly Necessary → Fides `essential`
- **C0002** - Performance → Fides `performance`
- **C0003** - Functional → Fides `functional`
- **C0004** - Targeting → Fides `advertising`

### Recommended Fides Notice Configuration

Create these notices in Fides Admin UI:

| Fides Notice Key | OneTrust Category | Adobe Purposes | ECID |
|------------------|-------------------|----------------|------|
| `essential` | C0001 | (none) | (none) |
| `performance` | C0002 | collect, measure | aa |
| `functional` | C0003 | personalize | target |
| `advertising` | C0004 | personalize, share | aam |

### Purpose Mapping for OneTrust Migration

```javascript
Fides.aep({
  purposeMapping: {
    performance: ['collect', 'measure'],    // C0002 → Analytics
    functional: ['personalize'],            // C0003 → Target
    advertising: ['personalize', 'share']   // C0004 → AAM
  }
});
```

Note: `essential` typically doesn't need Adobe consent tracking.

## Diagnostic Tools

### Check Adobe Configuration

```javascript
// Get current Adobe consent state
const aep = Fides.aep();
const consent = aep.consent();

console.log('Analytics approved:', consent.summary.analytics);
console.log('Personalization approved:', consent.summary.personalization);
console.log('Advertising approved:', consent.summary.advertising);

// Check ECID categories
console.log('ECID categories:', consent.ecidOptIn);
// { aa: true, target: false, aam: true }
```

### Check OneTrust Presence

```javascript
// Check if OneTrust is on the page
const otStatus = Fides.onetrust.status();

console.log('OneTrust detected:', otStatus.detected);
console.log('OneTrust categories:', otStatus.activeGroups);
// ['C0001', 'C0002', 'C0003', 'C0004']

console.log('Current consent:', otStatus.categoriesConsent);
// { C0001: true, C0002: false, C0003: true, C0004: false }
```

### Full Environment Status

```javascript
// Comprehensive diagnostics (NVIDIA demo environment)
const status = Fides.nvidia.status();

console.log('Fides consent keys:', status.fides.consentKeys);
console.log('Adobe ECID:', status.visitor.marketingCloudVisitorID);
console.log('OneTrust detected:', status.oneTrust?.detected);
console.log('Adobe Web SDK:', status.alloy?.configured);
```

## Troubleshooting

### Adobe Not Updating

**Symptom:** Fides consent changes but Adobe doesn't reflect them.

**Solution:** Check your `purposeMapping` matches your actual Fides consent keys.

```javascript
// 1. Check what Fides keys you have
console.log(Object.keys(window.Fides.consent));
// ['essential', 'ai_analytics', 'marketing', 'data_sales']

// 2. Map YOUR keys to Adobe purposes
Fides.aep({
  purposeMapping: {
    ai_analytics: ['collect', 'measure'],
    marketing: ['personalize', 'share'],
    data_sales: ['share']
  }
});
```

### OneTrust Not Migrating

**Symptom:** Fides doesn't initialize from OneTrust cookie.

**Check:**
1. OneTrust cookie exists: `Fides.onetrust.status()`
2. Cookie has `groups` parameter
3. Fides notice keys match OneTrust categories

### ECID Not Working

**Symptom:** `adobe.optIn` API not found.

**Cause:** Page is using modern Adobe Web SDK, not legacy ECID.

**Solution:** This is fine! The integration handles both:
- Modern: Uses `alloy.setConsent()`
- Legacy: Uses `adobe.optIn.approve()`

Check which you have:
```javascript
const status = Fides.nvidia.status();
console.log('Web SDK:', status.alloy?.configured);    // Modern
console.log('ECID:', status.optIn?.configured);       // Legacy
```

## Example: NVIDIA.com Configuration

```javascript
// NVIDIA uses OneTrust + Adobe ECID
// Their Fides notices: essential, performance, functional, advertising

const aep = Fides.aep({
  purposeMapping: {
    performance: ['collect', 'measure'],    // Analytics
    functional: ['personalize'],            // Target
    advertising: ['personalize', 'share']   // AAM
  }
});

// Integration is live - any Fides updates sync to Adobe automatically
```

## Testing the Integration

```javascript
// 1. Initialize integration
const aep = Fides.aep({ /* your config */ });

// 2. Check initial state
console.log(aep.consent());

// 3. Update Fides consent
window.Fides.consent.analytics = true;
window.dispatchEvent(new CustomEvent('FidesUpdated', {
  detail: { consent: window.Fides.consent }
}));

// 4. Wait 500ms, then verify Adobe updated
setTimeout(() => {
  console.log(aep.consent());
  // Should show analytics: true
}, 500);
```

## Production Deployment

In production, customers configure via Fides Admin UI:
1. Create notices (essential, performance, functional, advertising)
2. Configure Adobe destination with Org ID
3. Map notices to Adobe purposes
4. Deploy Fides.js - integration happens automatically

No manual `aep()` calls needed in production!

