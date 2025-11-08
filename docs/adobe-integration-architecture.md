# Adobe Experience Platform Integration Architecture

## Overview

The Adobe integration follows the same **unidirectional pattern** as other Fides integrations (GTM, Meta, Shopify):

**Flow: User Consent → Fides (source of truth) → Adobe Products**

Fides listens to its own consent events and pushes updates to Adobe. Adobe never writes back to Fides.

## Integration Patterns Comparison

| Integration | Direction | Mechanism |
|------------|-----------|-----------|
| **GTM** | Fides → GTM | Push to `window.dataLayer`, GTM template reads and controls tags |
| **Meta** | Fides → Meta | Call `fbq("consent", "grant/revoke")` |
| **Shopify** | Fides → Shopify | Push to Shopify Customer Privacy API |
| **Adobe** | Fides → Adobe | Call `alloy.setConsent()` / `adobe.optIn.approve()` |

**Fides is always the source of truth.** No bidirectional sync.

## Architecture

### 1. Configuration Layer

**Environment Variable:**
- Location: `/clients/privacy-center/.env`
- Variable: `FIDES_PRIVACY_CENTER__ADOBE_ORG_ID=ABC123@AdobeOrg`

**Privacy Center Pipeline:**
```
.env → loadEnvironmentVariables()
     → PrivacyCenterSettings
     → getClientSettings()
     → /api/fides.js bundle
```

### 2. Runtime Initialization

**Bundle Wrapper** (`/api/fides.js`):
```javascript
(function(){
  // 1. Load fides.js code
  // 2. Set window.Fides.config = {...}
  // 3. Set window.adobe_mc_orgid = "ABC123@AdobeOrg"  ← Critical!
  // 4. window.Fides.init()
})();
```

**Why this matters:**
- Adobe scripts require `window.adobe_mc_orgid` **before** they initialize
- Must be set in bundle wrapper, not in `init()` function
- Ensures Adobe Visitor API (ECID) can initialize properly

### 3. Integration API

**`Fides.aep()` Object:**

```typescript
interface AEPIntegration {
  dump: () => AEPDiagnostics;  // Get diagnostic data
  // Future: setConsent, sync, etc.
}
```

**Current Implementation (POC Phase):**
- `dump()`: Diagnostic function to inspect Adobe state
  - Checks for `window.alloy` (Web SDK)
  - Checks for `window.Visitor` (ECID)
  - Checks for `window.adobe.optIn` (legacy opt-in)
  - Reads Adobe cookies (AMCV, demdex, etc.)
  - Returns ECID and consent states

**Future Implementation:**
- Listen to `FidesReady`, `FidesUpdated` events
- Call `alloy.setConsent()` for modern Adobe Web SDK
- Call `adobe.optIn.approve()` for legacy ECID
- Support OneTrust migration
- Support configurable purpose mappings

## Files Modified

### Core Integration
- `clients/fides-js/src/integrations/aep.ts` - Adobe integration code
- `clients/fides-js/src/docs/fides.ts` - JSDoc for `Fides.aep()` API

### Type Definitions
- `clients/fides-js/src/lib/consent-types.ts` - Added `aep` to `FidesGlobal`
- `clients/fides-js/src/lib/init-utils.ts` - Added `window.adobe_mc_orgid` declaration

### Environment Configuration
- `clients/privacy-center/app/server-utils/PrivacyCenterSettings.ts` - `ADOBE_ORG_ID` interface
- `clients/privacy-center/app/server-utils/loadEnvironmentVariables.ts` - Load from env
- `clients/privacy-center/app/server-environment.ts` - Pass to client settings
- `clients/privacy-center/pages/api/fides-js.ts` - Inject into bundle wrapper

### Configuration Files
- `/clients/privacy-center/.env` - Customer-specific Org ID (not committed)
- `/docs/demo-setup-notes.md` - Setup instructions for demo environment

## Load Order Requirements

**Critical:** Fides.js must load **before** Adobe Launch:

```html
✅ CORRECT:
<script src="/api/fides.js"></script>
<script src="https://assets.adobedtm.com/.../launch.min.js"></script>

❌ WRONG:
<script src="https://assets.adobedtm.com/.../launch.min.js"></script>
<script src="/api/fides.js"></script>
```

If Adobe loads first, it will fail with:
```
Error: Visitor requires Adobe Marketing Cloud Org ID
```

## Testing

### 1. Verify Org ID is Set

```javascript
console.log(window.adobe_mc_orgid);
// Expected: "ABC123@AdobeOrg"
```

### 2. Check Diagnostics

```javascript
const aep = window.Fides.aep();
const diagnostics = aep.dump();
console.log(diagnostics);
```

**Expected Output:**
```json
{
  "timestamp": "2025-11-07T...",
  "alloy": { "configured": false },
  "visitor": {
    "configured": true,
    "marketingCloudVisitorID": "92176571735775623157607458525..."
  },
  "optIn": {
    "configured": true,
    "isApproved": {
      "aa": false,
      "target": false,
      "aam": false
    }
  },
  "cookies": {
    "amcv": "179643557%7CMCMID%7C92176..."
  }
}
```

### 3. Use Adobe Experience Platform Debugger

Chrome extension to validate:
- ECID is present
- Consent states are correct
- Analytics beacons fire (or don't) based on consent

## Next Steps (Future Implementation)

1. **Active Consent Sync** - Listen to Fides events and call Adobe APIs
2. **OneTrust Migration** - Parse `OptanonConsent` cookie
3. **Purpose Mapping** - Configurable Fides notices → Adobe purposes
4. **Admin UI** - Configure mappings without code changes
5. **Adobe Launch Rules** - Drop-in Launch rules for customers

## Security Considerations

- Adobe Org ID is **public** (appears in browser, not sensitive)
- No PII in consent payloads
- Consent strings are user-specific but not identifying
- ECID is Adobe's identifier, not Fides's responsibility

## References

- [Adobe Experience Platform Debugger](https://chrome.google.com/webstore/detail/adobe-experience-platform/bfnnokhpnncpkdmbokanobigaccjkpob)
- [Adobe Web SDK Consent v2](https://experienceleague.adobe.com/docs/experience-platform/edge/consent/supporting-consent.html)
- [Adobe ECID Opt-In Service](https://experienceleague.adobe.com/docs/id-service/using/implementation/opt-in-service/getting-started.html)
- [Fides GTM Integration](https://github.com/ethyca/fides) (for reference pattern)
