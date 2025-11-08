# Adobe Experience Platform Integration - Implementation Summary

## Overview

Implemented full Adobe Experience Platform (AEP) consent synchronization using the shared `subscribeToConsent` helper pattern.

## Architecture

### Shared Helper Pattern

Created `integration-utils.ts` with `subscribeToConsent()` helper that:
- ✅ Listens to `FidesReady` and `FidesUpdated` events
- ✅ Handles synthetic events for late-loading integrations
- ✅ Shared by Blueconic and Adobe (DRY principle)

### Event Flow

```
User Action → Fides Event → subscribeToConsent → pushConsentToAdobe → Adobe APIs
```

**Events Handled:**
- `FidesReady` - Initial consent (page load, always fires)
- `FidesUpdated` - Changed consent (user saves changes)
- Synthetic - Already-initialized Fides (late-loading integration)

## Implementation

### 1. Core Integration (`aep.ts`)

**Features:**
- ✅ Adobe Web SDK (Consent v2) - modern
- ✅ ECID Opt-In Service - legacy
- ✅ Configurable purpose mapping
- ✅ Debug logging option
- ✅ Full diagnostic API

**Default Purpose Mapping:**
```typescript
{
  analytics: ['collect', 'measure'],    // → Adobe AA
  functional: ['personalize'],          // → Adobe Target
  advertising: ['share', 'personalize'] // → Adobe AAM
}
```

**ECID Category Mapping:**
```typescript
{
  analytics: 'aa',      // Analytics
  functional: 'target', // Target
  advertising: 'aam'    // Audience Manager
}
```

### 2. Integration API

```typescript
const aep = Fides.aep(options);

// Options
interface AEPOptions {
  purposeMapping?: { [fidesKey: string]: string[] };
  debug?: boolean;
}

// Returns
interface AEPIntegration {
  dump: () => AEPDiagnostics; // Get diagnostic data
}
```

### 3. Diagnostic API

```typescript
const diagnostics = aep.dump();

// Returns comprehensive Adobe state:
{
  timestamp: string;
  alloy: { configured, consent, identity, config };
  visitor: { configured, marketingCloudVisitorID, ... };
  optIn: { configured, categories, isApproved };
  cookies: { ecid, amcv, demdex, ... };
  launch: { configured, property, environment };
  analytics: { configured, reportSuite, trackingServer };
}
```

## Files Modified

### New Files
1. **`integrations/integration-utils.ts`** - Shared helper for consent subscriptions
2. **`integrations/aep.ts`** - Full Adobe integration

### Updated Files
3. **`integrations/blueconic.ts`** - Refactored to use shared helper
4. **`lib/init-utils.ts`** - Added `aep` to global Fides object
5. **`docs/fides.ts`** - Added JSDoc documentation for `Fides.aep()`
6. **`lib/consent-types.ts`** - Already had `aep` type (from earlier)

### Environment Configuration (Already Done)
7. **`clients/privacy-center/.env`** - `FIDES_PRIVACY_CENTER__ADOBE_ORG_ID`
8. **`clients/privacy-center/pages/api/fides-js.ts`** - Inject `window.adobe_mc_orgid`

## Usage Examples

### Basic

```html
<head>
  <script src="/api/fides.js"></script>
  <script>Fides.aep()</script>
  <script src="https://assets.adobedtm.com/.../launch.min.js"></script>
</head>
```

### With Custom Mapping

```javascript
Fides.aep({
  purposeMapping: {
    analytics: ['collect', 'measure'],
    marketing: ['personalize', 'share'],
    essential: [] // No Adobe purposes for essential
  },
  debug: true
});
```

### Diagnostics

```javascript
const aep = Fides.aep();
const diagnostics = aep.dump();

console.log('ECID:', diagnostics.visitor.marketingCloudVisitorID);
console.log('Adobe Web SDK:', diagnostics.alloy.configured ? 'Yes' : 'No');
console.log('Analytics Consent:', diagnostics.optIn.isApproved.aa);
```

## Testing Checklist

### Prerequisites
- ✅ `FIDES_PRIVACY_CENTER__ADOBE_ORG_ID` set in `/clients/privacy-center/.env`
- ✅ Privacy Center restarted
- ✅ Fides.js rebuilt (if testing locally)

### Test Scenarios

**1. Page Load (First-Time Visitor)**
```javascript
// FidesReady should fire with default consent
// Adobe should receive consent state immediately
const aep = Fides.aep({ debug: true });
// Check console for: "[Fides Adobe] Pushing consent to Adobe"
```

**2. Page Load (Returning Visitor)**
```javascript
// FidesReady should fire with saved consent from cookie
// Adobe should receive saved consent state
```

**3. User Changes Consent**
```javascript
// User clicks "Save" in modal
// FidesUpdated should fire
// Adobe should receive updated consent
// Check console for: "[Fides Adobe] Sent consent to Adobe Web SDK"
```

**4. Late Integration (Call after init)**
```javascript
// Fides already initialized
Fides.aep();
// Synthetic event should fire immediately
// Adobe should receive current consent state
```

**5. Diagnostics**
```javascript
const aep = Fides.aep();
const diagnostics = aep.dump();

// Verify:
assert(diagnostics.visitor.configured === true);
assert(diagnostics.visitor.marketingCloudVisitorID !== undefined);
assert(diagnostics.cookies.ecid !== undefined);
```

### Adobe Experience Platform Debugger

Install Chrome extension: [Adobe Experience Platform Debugger](https://chrome.google.com/webstore/detail/adobe-experience-platform/bfnnokhpnncpkdmbokanobigaccjkpob)

**Verify:**
- ✅ ECID present
- ✅ Consent state matches Fides
- ✅ Analytics beacons fire/blocked based on consent

## Benefits of This Implementation

✅ **DRY** - Shared helper reduces duplication
✅ **Consistent** - Same pattern as Blueconic, Shopify
✅ **Maintainable** - Single source of truth for event handling
✅ **Extensible** - Easy to add more integrations
✅ **Testable** - Helper and integration independently testable
✅ **Debuggable** - Debug mode + diagnostic API
✅ **Flexible** - Configurable purpose mapping
✅ **Complete** - Supports modern + legacy Adobe

## Next Steps

### Phase 2 (Future)
- [ ] OneTrust migration support
- [ ] Admin UI for purpose mapping configuration
- [ ] Adobe Launch rule templates (drop-in for customers)
- [ ] Regional consent defaults
- [ ] IAB TCF/GPP string forwarding
- [ ] Server-side Adobe integration

### Documentation
- [ ] Customer-facing tutorial
- [ ] Adobe Launch configuration guide
- [ ] Migration guide (OneTrust → Fides)

## References

- [Adobe Web SDK Consent v2](https://experienceleague.adobe.com/docs/experience-platform/edge/consent/supporting-consent.html)
- [Adobe ECID Opt-In Service](https://experienceleague.adobe.com/docs/id-service/using/implementation/opt-in-service/getting-started.html)
- [Fides Events Documentation](../clients/fides-js/src/docs/fides-event.ts)
