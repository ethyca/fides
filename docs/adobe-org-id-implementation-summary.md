# Adobe Org ID Implementation Summary

## Problem
Adobe Visitor API requires `window.adobe_mc_orgid` to be set **before** Adobe Launch scripts initialize, otherwise it throws: `"Visitor requires Adobe Marketing Cloud Org ID"`

## Solution
Set `window.adobe_mc_orgid` directly in the Fides.js bundle wrapper, before `Fides.init()` runs.

## Implementation

### 1. Environment Variable (One Place Only)

**File:** `/clients/privacy-center/.env`

```bash
FIDES_PRIVACY_CENTER__ADOBE_ORG_ID=F207D74D549850760A4C98C6@AdobeOrg
```

### 2. Privacy Center Pipeline (3 files)

Read the environment variable and pass it through to the bundle generator:

1. **`clients/privacy-center/app/server-utils/PrivacyCenterSettings.ts`**
   - Defines `ADOBE_ORG_ID: string | null` in interface

2. **`clients/privacy-center/app/server-utils/loadEnvironmentVariables.ts`**
   - Reads `process.env.FIDES_PRIVACY_CENTER__ADOBE_ORG_ID`

3. **`clients/privacy-center/app/server-environment.ts`**
   - Passes to `PrivacyCenterClientSettings`

### 3. Bundle Injection (The Core Fix)

**File:** `clients/privacy-center/pages/api/fides-js.ts`

```typescript
window.Fides.config = ${fidesConfigJSON};
${
  environment.settings.ADOBE_ORG_ID
    ? `// Set Adobe Marketing Cloud Org ID before init (required by Adobe Visitor API)
window.adobe_mc_orgid = ${JSON.stringify(environment.settings.ADOBE_ORG_ID)};`
    : ""
}
${skipInitialization ? "" : `window.Fides.init();`}
```

This sets `window.adobe_mc_orgid` **immediately** when fides.js loads, before any initialization.

### 4. TypeScript Declaration

**File:** `clients/fides-js/src/lib/init-utils.ts`

```typescript
declare global {
  interface Window {
    adobe_mc_orgid?: string; // Adobe Marketing Cloud Org ID (set by Fides for Adobe integrations)
  }
}
```

## What Was Removed (Cleanup)

### ❌ Removed Unnecessary Code

1. **Unused Config Option**
   - Removed `adobeOrgId?: string | null` from `FidesInitOptions` interface
   - Was never read or used anywhere

2. **Duplicate Init Assignments**
   - Removed `window.adobe_mc_orgid = config.options.adobeOrgId` from:
     - `fides.ts` init function
     - `fides-tcf.ts` init function
     - `fides-headless.ts` init function
   - These were redundant and happened too late

3. **Wrong .env File**
   - Removed from `/Users/thabo/Repos/fides/.env` (root - not used by Privacy Center)
   - Only needed in `/Users/thabo/Repos/fides/clients/privacy-center/.env`

## Execution Flow

```
1. Developer sets FIDES_PRIVACY_CENTER__ADOBE_ORG_ID in /clients/privacy-center/.env
   ↓
2. Privacy Center reads it (loadEnvironmentVariables)
   ↓
3. Privacy Center generates /api/fides.js bundle with adobe_mc_orgid injection
   ↓
4. Browser loads fides.js → window.adobe_mc_orgid = "ABC@AdobeOrg" (BEFORE init)
   ↓
5. Browser loads Adobe Launch → Visitor API uses window.adobe_mc_orgid ✅
   ↓
6. Fides.aep().dump() works correctly with ECID data ✅
```

## Load Order Requirements

**CRITICAL:** Fides.js must load before Adobe Launch:

```html
<!-- ✅ CORRECT -->
<script src="http://localhost:3001/api/fides.js"></script>
<script src="https://assets.adobedtm.com/launch-xxx.min.js"></script>

<!-- ❌ WRONG -->
<script src="https://assets.adobedtm.com/launch-xxx.min.js"></script>
<script src="http://localhost:3001/api/fides.js"></script>
```

## Testing

```javascript
// Should be set before Adobe scripts load
console.log(window.adobe_mc_orgid); // "F207D74D549850760A4C98C6@AdobeOrg"

// Should work without errors
const aep = window.Fides.aep();
const diagnostics = aep.dump();
console.log(diagnostics.visitor); // Should include marketingCloudVisitorID (ECID)
```

## Files Changed

### Modified (8 files)
1. `clients/fides-js/src/lib/init-utils.ts` - Window type declaration
2. `clients/fides-js/src/integrations/aep.ts` - Fixed getInstance() call, added error handling
3. `clients/privacy-center/app/server-utils/PrivacyCenterSettings.ts` - Added ADOBE_ORG_ID setting
4. `clients/privacy-center/app/server-utils/loadEnvironmentVariables.ts` - Read env var
5. `clients/privacy-center/app/server-environment.ts` - Pass to client
6. `clients/privacy-center/pages/api/fides-js.ts` - Bundle injection (core fix)
7. `clients/privacy-center/.env` - Added FIDES_PRIVACY_CENTER__ADOBE_ORG_ID

### Created (2 files)
1. `docs/demo-setup-notes.md` - Setup instructions
2. `docs/adobe-org-id-implementation-summary.md` - This file

## Key Lessons

1. **Timing matters**: Setting `window.adobe_mc_orgid` in `init()` was too late
2. **One source of truth**: Bundle wrapper is the right place to inject global variables
3. **Environment files**: Next.js apps load `.env` from their own directory, not the repo root
4. **Simplicity**: Direct injection beats complex config pipelines
