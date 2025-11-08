# Adobe Experience Platform (Tags/Launch) Integration - PRD Implementation

**Document Version:** 1.0
**Date:** November 5, 2025
**Status:** Implementation Ready
**PRD Reference:** 221515.pdf
**Related Docs:** [Comprehensive Adobe Plan](./adobe-tag-manager-implementation-plan.md) (broader scope, future phases)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Objectives](#objectives)
3. [Integration Modes](#integration-modes)
4. [Technical Architecture](#technical-architecture)
5. [Implementation Phases](#implementation-phases)
6. [Data Elements & Rules](#data-elements--rules)
7. [Consent Mapping](#consent-mapping)
8. [OneTrust Migration](#onetrust-migration)
9. [Admin UI Requirements](#admin-ui-requirements)
10. [Testing Strategy](#testing-strategy)
11. [Success Criteria](#success-criteria)
12. [Timeline](#timeline)

---

## Executive Summary

This document outlines the implementation of Adobe Experience Platform (AEP) Data Collection integration for Fides CMP, achieving **parity with OneTrust's Adobe integration** and enabling seamless migration for existing OneTrust customers.

### Core Deliverables

1. **Three Integration Modes**: Web SDK (modern), ECID Opt-In (legacy), Tag Suppression
2. **OneTrust Migration Support**: Parse `OptanonConsent` cookie with configurable mappings
3. **Admin UI Configuration**: Destination tile with mapping tables and regional defaults
4. **Drop-in Adobe Launch Templates**: Data elements and rules mirroring OneTrust patterns

### Key Difference from Comprehensive Plan

This implementation focuses specifically on **OneTrust parity and migration**, not general Adobe integration. The [comprehensive plan](./adobe-tag-manager-implementation-plan.md) remains as reference for future enhancements.

---

## Objectives

### Primary Goal

Enable Fides CMP to control Adobe Experience Platform consent behavior using Adobe's "Consent Mode", with complete OneTrust feature parity.

### Must-Have Requirements

| Requirement | Priority | Notes |
|-------------|----------|-------|
| Adobe Web SDK Consent v2 | MUST HAVE | Modern `setConsent()` API |
| ECID Opt-In Service | MUST HAVE | Legacy AppMeasurement support |
| Adobe Tags Rule Templates | MUST HAVE | Drop-in data elements + rules |
| Fides → Adobe Mapping | MUST HAVE | Default mappings + Admin UI overrides |
| OneTrust Migration | MUST HAVE | Parse `OptanonConsent`, use `ot_fides_mapping` |
| IAB TCF/GPP Forwarding | SHOULD HAVE | Forward IAB strings to Adobe |
| Regional Defaults | SHOULD HAVE | Region-based consent defaults |
| Diagnostics & Validation | SHOULD HAVE | Adobe Platform Debugger support |
| Admin UI Configuration | SHOULD HAVE | Destination pane with mappings |

### Success Metrics

- ✅ Existing OneTrust + Adobe customers can migrate without re-consent
- ✅ All three integration modes work correctly
- ✅ Admin UI allows configuration without code changes
- ✅ Adobe Platform Debugger shows correct consent states
- ✅ Documentation matches OneTrust's quality

---

## Integration Modes

Fides will support **three distinct integration modes** that can be enabled separately:

### Mode A: Adobe Web SDK (Consent Standard v2)

**Target:** Modern Adobe Experience Platform stacks (default)

**Mechanism:** Call `alloy("setConsent", {...})` when Fides consent updates

**Use Case:** Customers using Adobe Experience Platform Web SDK

**Adobe Products Supported:**
- Adobe Analytics (via Web SDK)
- Adobe Target
- Adobe Audience Manager
- Adobe Experience Platform

**Implementation:**
```javascript
// When Fides consent updates
alloy("setConsent", {
  consent: [{
    standard: "Adobe",
    version: "2.0",
    value: {
      collect: { val: "y" },    // analytics consent
      measure: { val: "y" },    // analytics consent
      personalize: { val: "n" }, // functional/target consent
      share: { val: "n" }        // advertising consent
    }
  }],
  metadata: {
    iab: window.Fides.fides_string  // TCF/GPP string if available
  }
});
```

**Adobe Launch Rule:**
- **Event:** Custom Event → `fides:ready` or `fides:updated`
- **Condition:** Always true
- **Action:** Adobe Experience Platform Web SDK → Update Consent

---

### Mode B: ECID Opt-In Service

**Target:** Legacy sites using AppMeasurement/Analytics.js

**Mechanism:** Call `adobe.optIn.approve()` or `adobe.optIn.deny()` per category

**Use Case:** Customers still using legacy Adobe Analytics (pre-Web SDK)

**Adobe Products Supported:**
- Adobe Analytics (AppMeasurement)
- Adobe Target (mbox.js or at.js)
- Adobe Audience Manager (DIL)

**Categories:**
- `aa` - Adobe Analytics
- `target` - Adobe Target
- `aam` - Adobe Audience Manager

**Implementation:**
```javascript
// After FidesReady event
var consent = window.Fides.consent;
var optInCategories = {
  analytics: "aa",
  functional: "target",
  advertising: "aam"
};

for (var noticeKey in optInCategories) {
  var category = optInCategories[noticeKey];
  if (consent[noticeKey]) {
    adobe.optIn.approve(category, true);
  } else {
    adobe.optIn.deny(category, true);
  }
}

// Trigger completion
adobe.optIn.complete();
```

**Adobe Launch Rule:**
- **Event:** Custom Event → `fides:ready` or `fides:updated`
- **Condition:** Check if `adobe.optIn` exists
- **Action:** Custom Code (opt-in logic above)

---

### Mode C: Tag Suppression via Data Elements

**Target:** Advanced users who want fine-grained control

**Mechanism:** Adobe Data Elements expose Fides consent; rules use conditions to fire/suppress tags

**Use Case:**
- Complex tag management scenarios
- Multiple tag vendors beyond Adobe
- Custom consent logic

**Implementation:**
- Create Data Elements that read `window.Fides.consent.*`
- Use Data Elements in Rule Conditions
- Tags only fire when conditions evaluate to true

**Example Data Element:** `Fides Analytics Consent`
```javascript
return window.Fides && window.Fides.consent && window.Fides.consent.analytics === true;
```

**Example Rule Condition:**
```
%Fides Analytics Consent% equals true
```

---

## Technical Architecture

### Runtime Sequence

```
┌─────────────────────────────────────────────────────────────────┐
│                         Page Load                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. FidesJS Loads First                                          │
│     - Reads consent from cookie (if exists)                      │
│     - Reads OptanonConsent cookie (if migrating)                 │
│     - Initializes consent state                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. Adobe Libraries Load                                         │
│     - Web SDK defaults to consent="pending"                      │
│     - ECID defaults to optIn state="pending"                     │
│     - No tags fire yet                                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. Fides Emits "FidesReady" Event                               │
│     - window.Fides.consent populated                             │
│     - window.Fides.fides_string available (if TCF/GPP)           │
│     - Custom event dispatched                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. Adobe Launch Rule Fires                                      │
│     - Event: fides:ready                                         │
│     - Action: Set Adobe Consent                                  │
│     - Calls setConsent() or optIn.approve()/deny()               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. Adobe Updates Consent State                                  │
│     - Consent changes from "pending" to "in"/"out"               │
│     - Queued Adobe events are released or discarded              │
│     - Tags begin firing (if consent granted)                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  6. User Updates Consent (Optional)                              │
│     - Fides emits "FidesUpdated" event                           │
│     - Adobe Launch rule fires again                              │
│     - Adobe consent state updates                                │
│     - Tags fire/stop based on new consent                        │
└─────────────────────────────────────────────────────────────────┘
```

### Component Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                        Fides Admin UI                             │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │   Adobe Experience Platform Destination                 │    │
│  │                                                           │    │
│  │   [✓] Enable Web SDK (Consent v2)                       │    │
│  │   [✓] Enable ECID Opt-In (Legacy)                       │    │
│  │   [ ] Enable Tag Suppression Only                       │    │
│  │                                                           │    │
│  │   Consent Mapping:                                       │    │
│  │   ┌──────────────┬──────────────┬─────────────┐        │    │
│  │   │ Fides Notice │ Adobe Purpose│ ECID Category│        │    │
│  │   ├──────────────┼──────────────┼─────────────┤        │    │
│  │   │ analytics    │ collect,     │ aa           │        │    │
│  │   │              │ measure      │              │        │    │
│  │   │ functional   │ personalize  │ target       │        │    │
│  │   │ advertising  │ share        │ aam          │        │    │
│  │   └──────────────┴──────────────┴─────────────┘        │    │
│  │                                                           │    │
│  │   OneTrust Migration:                                    │    │
│  │   [✓] Enable OptanonConsent parsing                     │    │
│  │   Mapping: C0001→analytics, C0002→advertising ...       │    │
│  └─────────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────────┘
                                │
                                │ Configuration API
                                ▼
┌───────────────────────────────────────────────────────────────────┐
│                      FidesJS SDK (Browser)                        │
│                                                                   │
│  window.Fides = {                                                │
│    consent: { analytics: true, advertising: false, ... },        │
│    fides_string: "CPX...",  // TCF/GPP string if applicable      │
│    adobe: function(options) { /* integration setup */ }          │
│  }                                                                │
│                                                                   │
│  Events Dispatched:                                              │
│    - fides:ready      (initial consent loaded)                   │
│    - fides:updated    (user changed consent)                     │
└───────────────────────────────────────────────────────────────────┘
                                │
                                │ Custom Events
                                ▼
┌───────────────────────────────────────────────────────────────────┐
│              Adobe Experience Platform Launch                     │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Data Elements (expose Fides consent)                    │    │
│  │   - FidesConsentObject                                  │    │
│  │   - FidesActiveKeys                                     │    │
│  │   - FidesConsentString (TCF/GPP)                        │    │
│  │   - Fides Analytics Consent                             │    │
│  │   - Fides Advertising Consent                           │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Rules                                                    │    │
│  │                                                           │    │
│  │  1. Set Adobe Web SDK Consent                           │    │
│  │     Event: fides:ready, fides:updated                   │    │
│  │     Action: alloy("setConsent", {...})                  │    │
│  │                                                           │    │
│  │  2. Set ECID Opt-In                                     │    │
│  │     Event: fides:ready, fides:updated                   │    │
│  │     Action: adobe.optIn.approve/deny(...)               │    │
│  │                                                           │    │
│  │  3. Fire Analytics (conditional)                        │    │
│  │     Event: Page Load                                     │    │
│  │     Condition: %Fides Analytics Consent% = true         │    │
│  │     Action: Adobe Analytics - Send Beacon               │    │
│  └─────────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────┐
│                    Adobe Products                                 │
│                                                                   │
│  - Adobe Analytics    (fires only with analytics consent)        │
│  - Adobe Target       (fires only with functional consent)       │
│  - Audience Manager   (fires only with advertising consent)      │
└───────────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Core Integration (Weeks 1-3)

**Goal:** Basic Fides → Adobe integration for all three modes

#### 1.1 FidesJS Adobe Integration Module

**File:** `clients/fides-js/src/integrations/adobe.ts`

**Key Features:**
- Detect Adobe Web SDK (`alloy`) vs ECID (`adobe.optIn`) vs neither
- Dispatch custom events (`fides:ready`, `fides:updated`) for Adobe Launch
- Provide helper to map Fides consent → Adobe purposes
- Support IAB TCF/GPP string forwarding

**Core Functions:**

```typescript
export interface AdobeIntegrationOptions {
  // Which modes to enable
  enableWebSDK?: boolean;        // Default: true if alloy exists
  enableECID?: boolean;          // Default: true if adobe.optIn exists
  enableDataElements?: boolean;  // Default: true

  // Custom consent mappings (override defaults)
  webSDKMapping?: AdobeWebSDKMapping;
  ecidMapping?: AdobeECIDMapping;

  // Event configuration
  eventPrefix?: string;          // Default: "fides"
}

export interface AdobeWebSDKMapping {
  [adobePurpose: string]: string[];  // Adobe purpose → [Fides notice keys]
}

export interface AdobeECIDMapping {
  [ecidCategory: string]: string[];  // ECID category → [Fides notice keys]
}

// Default mappings (based on OneTrust parity)
const DEFAULT_WEBSDK_MAPPING: AdobeWebSDKMapping = {
  collect: ["analytics"],
  measure: ["analytics"],
  personalize: ["functional"],
  share: ["advertising", "data_sales_and_sharing"]
};

const DEFAULT_ECID_MAPPING: AdobeECIDMapping = {
  aa: ["analytics"],
  target: ["functional"],
  aam: ["advertising", "data_sales_and_sharing"]
};

/**
 * Initialize Adobe Experience Platform integration
 */
export const adobe = (options: AdobeIntegrationOptions = {}) => {
  const opts = {
    enableWebSDK: options.enableWebSDK ?? (typeof window.alloy !== "undefined"),
    enableECID: options.enableECID ?? (typeof window.adobe?.optIn !== "undefined"),
    enableDataElements: options.enableDataElements ?? true,
    eventPrefix: options.eventPrefix ?? "fides",
    webSDKMapping: options.webSDKMapping ?? DEFAULT_WEBSDK_MAPPING,
    ecidMapping: options.ecidMapping ?? DEFAULT_ECID_MAPPING,
  };

  // Set up event listeners
  setupFidesEventListeners(opts);

  // If Fides already initialized, trigger immediately
  if (window.Fides?.initialized) {
    handleFidesReady(window.Fides.consent, opts);
  }
};

function setupFidesEventListeners(opts: Required<AdobeIntegrationOptions>) {
  window.addEventListener("FidesReady", (event) => {
    handleFidesReady(event.detail.consent, opts);
  });

  window.addEventListener("FidesUpdated", (event) => {
    handleFidesUpdated(event.detail.consent, opts);
  });
}

function handleFidesReady(consent: NoticeConsent, opts: Required<AdobeIntegrationOptions>) {
  // Mode A: Web SDK
  if (opts.enableWebSDK) {
    setAdobeWebSDKConsent(consent, opts.webSDKMapping);
  }

  // Mode B: ECID Opt-In
  if (opts.enableECID) {
    setAdobeECIDOptIn(consent, opts.ecidMapping);
  }

  // Mode C: Dispatch custom event for Launch rules
  dispatchAdobeLaunchEvent(`${opts.eventPrefix}:ready`, {
    consent,
    fides_string: window.Fides?.fides_string,
  });
}

function handleFidesUpdated(consent: NoticeConsent, opts: Required<AdobeIntegrationOptions>) {
  // Same logic as handleFidesReady, but for updates
  if (opts.enableWebSDK) {
    setAdobeWebSDKConsent(consent, opts.webSDKMapping);
  }

  if (opts.enableECID) {
    setAdobeECIDOptIn(consent, opts.ecidMapping);
  }

  dispatchAdobeLaunchEvent(`${opts.eventPrefix}:updated`, {
    consent,
    fides_string: window.Fides?.fides_string,
  });
}

function setAdobeWebSDKConsent(
  consent: NoticeConsent,
  mapping: AdobeWebSDKMapping
) {
  if (typeof window.alloy !== "function") {
    console.warn("Adobe Web SDK (alloy) not found");
    return;
  }

  // Build Adobe Consent v2 payload
  const adobePurposes = Object.entries(mapping).map(([purpose, noticeKeys]) => {
    const hasConsent = noticeKeys.some(key =>
      consent[key] === true || consent[key] === "opt_in" || consent[key] === "acknowledge"
    );

    return {
      [purpose]: {
        val: hasConsent ? "y" : "n"
      }
    };
  }).reduce((acc, curr) => ({ ...acc, ...curr }), {});

  const payload = {
    consent: [{
      standard: "Adobe",
      version: "2.0",
      value: adobePurposes
    }]
  };

  // Include IAB string if available
  if (window.Fides?.fides_string) {
    payload.consent[0].metadata = {
      iab: window.Fides.fides_string
    };
  }

  window.alloy("setConsent", payload);
}

function setAdobeECIDOptIn(
  consent: NoticeConsent,
  mapping: AdobeECIDMapping
) {
  if (!window.adobe?.optIn) {
    console.warn("Adobe ECID Opt-In Service not found");
    return;
  }

  Object.entries(mapping).forEach(([category, noticeKeys]) => {
    const hasConsent = noticeKeys.some(key =>
      consent[key] === true || consent[key] === "opt_in" || consent[key] === "acknowledge"
    );

    if (hasConsent) {
      window.adobe.optIn.approve(category, true);
    } else {
      window.adobe.optIn.deny(category, true);
    }
  });

  // Signal completion
  window.adobe.optIn.complete();
}

function dispatchAdobeLaunchEvent(eventName: string, detail: any) {
  // Dispatch custom event for Adobe Launch rules
  const event = new CustomEvent(eventName, { detail });
  window.dispatchEvent(event);

  // Also try _satellite.track if available
  if (window._satellite?.track) {
    window._satellite.track(eventName, detail);
  }
}
```

#### 1.2 Wire Up Integration

**File:** `clients/fides-js/src/lib/init-utils.ts`

```typescript
import { adobe } from "../integrations/adobe";

export const getCoreFides = ({ tcfEnabled = false }): FidesGlobal => {
  return {
    // ...existing properties
    adobe,
    gtm,
    shopify,
    meta,
    blueconic,
    // ...
  };
};
```

#### 1.3 TypeScript Definitions

**File:** `clients/fides-js/src/lib/consent-types.ts`

```typescript
import type { adobe } from "../integrations/adobe";

export interface FidesGlobal extends Omit<Fides, "init"> {
  adobe: typeof adobe;
  gtm: typeof gtm;
  // ...
}
```

**File:** `clients/fides-js/src/docs/fides.ts`

```typescript
/**
 * Enable Adobe Experience Platform (Tags/Launch) integration.
 * Supports three modes: Web SDK, ECID Opt-In, and Tag Suppression.
 *
 * @param options - Configuration options
 * @param options.enableWebSDK - Enable Adobe Web SDK Consent v2 (default: auto-detect)
 * @param options.enableECID - Enable ECID Opt-In Service for legacy (default: auto-detect)
 * @param options.enableDataElements - Dispatch events for data elements (default: true)
 * @param options.webSDKMapping - Custom Adobe purpose mapping
 * @param options.ecidMapping - Custom ECID category mapping
 * @param options.eventPrefix - Event name prefix (default: "fides")
 *
 * @example
 * Basic usage (auto-detect modes):
 * ```html
 * <script src="fides.js"></script>
 * <script>Fides.adobe()</script>
 * ```
 *
 * @example
 * Custom mapping:
 * ```javascript
 * Fides.adobe({
 *   webSDKMapping: {
 *     collect: ['analytics'],
 *     measure: ['analytics'],
 *     share: ['advertising', 'data_sales']
 *   }
 * });
 * ```
 */
adobe: (options?: {
  enableWebSDK?: boolean;
  enableECID?: boolean;
  enableDataElements?: boolean;
  webSDKMapping?: Record<string, string[]>;
  ecidMapping?: Record<string, string[]>;
  eventPrefix?: string;
}) => void;
```

---

### Phase 2: OneTrust Migration (Weeks 3-4)

**Goal:** Parse OneTrust cookies and migrate consent seamlessly

#### 2.1 OneTrust Migration Module

**File:** `clients/fides-js/src/lib/onetrust-migration.ts`

```typescript
export interface OneTrustMigrationConfig {
  // OneTrust category → Fides notice key mapping
  categoryMapping: Record<string, string>;

  // Whether to preserve OneTrust cookie after migration
  preserveOneTrustCookie?: boolean;
}

/**
 * Parse OptanonConsent cookie and extract consent groups
 */
export function parseOptanonConsent(): {
  activeGroups: string[];
  timestamp: string;
} | null {
  const cookie = document.cookie
    .split('; ')
    .find(row => row.startsWith('OptanonConsent='));

  if (!cookie) return null;

  const value = decodeURIComponent(cookie.split('=')[1]);
  const params = new URLSearchParams(value);

  const groups = params.get('groups');
  if (!groups) return null;

  // Groups format: "C0001:1,C0002:0,C0003:1,C0004:1"
  const activeGroups = groups
    .split(',')
    .filter(g => g.endsWith(':1'))
    .map(g => g.split(':')[0]);

  return {
    activeGroups,
    timestamp: params.get('datestamp') || new Date().toISOString()
  };
}

/**
 * Get OneTrust → Fides mapping from ot_fides_mapping global
 */
export function getOneTrustFidesMapping(): Record<string, string> {
  // Check for global mapping configuration
  const mapping = (window as any).ot_fides_mapping;

  if (mapping) return mapping;

  // Default mapping (OneTrust categories → Fides notices)
  return {
    'C0001': 'necessary',           // Strictly Necessary
    'C0002': 'functional',          // Performance/Functional
    'C0003': 'analytics',           // Analytics
    'C0004': 'advertising',         // Targeting/Advertising
    'C0005': 'data_sales_and_sharing'  // Social Media / Data Sales
  };
}

/**
 * Migrate OneTrust consent to Fides format
 */
export function migrateOneTrustConsent(
  config?: Partial<OneTrustMigrationConfig>
): NoticeConsent | null {
  const optanonData = parseOptanonConsent();
  if (!optanonData) return null;

  const mapping = config?.categoryMapping ?? getOneTrustFidesMapping();
  const fidesConsent: NoticeConsent = {};

  // Map OneTrust categories to Fides notices
  for (const [oneTrustCat, fidesNotice] of Object.entries(mapping)) {
    const hasConsent = optanonData.activeGroups.includes(oneTrustCat);
    fidesConsent[fidesNotice] = hasConsent;
  }

  return fidesConsent;
}
```

#### 2.2 Integrate Migration into Fides Init

**File:** `clients/fides-js/src/lib/initialize.ts`

```typescript
import { migrateOneTrustConsent } from './onetrust-migration';

export async function initialize(config: FidesConfig) {
  // ...existing init logic

  // Check for OneTrust migration
  const migratedConsent = migrateOneTrustConsent(config.oneTrustMigration);

  if (migratedConsent) {
    // Use migrated consent as initial state
    console.log('[Fides] Migrating consent from OneTrust');

    // Merge with any existing Fides consent
    const existingConsent = getFidesConsentCookie();
    const mergedConsent = {
      ...migratedConsent,
      ...(existingConsent?.consent ?? {})
    };

    // Don't show banner if we have migrated consent
    config.options.fidesDisableBanner = true;

    // Save to Fides cookie
    saveFidesCookie({
      consent: mergedConsent,
      identity: existingConsent?.identity ?? {},
      fides_meta: {
        ...existingConsent?.fides_meta,
        migratedFrom: 'OneTrust',
        migratedAt: new Date().toISOString()
      }
    });
  }

  // ...continue with normal init
}
```

#### 2.3 Admin UI Configuration for Migration

Store OneTrust mapping in backend:

```python
# Backend model for Adobe destination configuration
class AdobeDestinationConfig(Base):
    __tablename__ = "adobe_destination_config"

    id = Column(String, primary_key=True)
    property_id = Column(String, ForeignKey("property.id"))

    # Integration modes
    enable_web_sdk = Column(Boolean, default=True)
    enable_ecid = Column(Boolean, default=False)
    enable_tag_suppression = Column(Boolean, default=True)

    # OneTrust migration mapping (JSON)
    onetrust_mapping = Column(JSON, default={
        "C0001": "necessary",
        "C0002": "functional",
        "C0003": "analytics",
        "C0004": "advertising",
        "C0005": "data_sales_and_sharing"
    })

    # Consent purpose mapping (JSON)
    web_sdk_mapping = Column(JSON, default={
        "collect": ["analytics"],
        "measure": ["analytics"],
        "personalize": ["functional"],
        "share": ["advertising", "data_sales_and_sharing"]
    })

    ecid_mapping = Column(JSON, default={
        "aa": ["analytics"],
        "target": ["functional"],
        "aam": ["advertising", "data_sales_and_sharing"]
    })
```

---

### Phase 3: Admin UI (Weeks 4-5)

**Goal:** Configuration interface for Adobe destination

#### 3.1 Adobe Destination Tile

**File:** `clients/admin-ui/src/features/destinations/AdobeDestinationCard.tsx`

```tsx
import { Card, Switch, Table, Button } from "fidesui";

export const AdobeDestinationCard = ({ property }: { property: Property }) => {
  const [config, setConfig] = useState<AdobeDestinationConfig>();

  return (
    <Card>
      <CardHeader>
        <Heading>Adobe Experience Platform</Heading>
        <Text>Integrate Fides consent with Adobe Tags (Launch)</Text>
      </CardHeader>

      <CardBody>
        {/* Integration Modes */}
        <Section>
          <SectionHeading>Integration Modes</SectionHeading>

          <Switch
            isChecked={config?.enable_web_sdk}
            onChange={(e) => setConfig({ ...config, enable_web_sdk: e.target.checked })}
          >
            Adobe Web SDK (Consent v2)
          </Switch>
          <Text fontSize="sm" color="gray.600">
            Modern Adobe Experience Platform stacks
          </Text>

          <Switch
            isChecked={config?.enable_ecid}
            onChange={(e) => setConfig({ ...config, enable_ecid: e.target.checked })}
          >
            ECID Opt-In Service (Legacy)
          </Switch>
          <Text fontSize="sm" color="gray.600">
            For AppMeasurement / Analytics.js implementations
          </Text>

          <Switch
            isChecked={config?.enable_tag_suppression}
            onChange={(e) => setConfig({ ...config, enable_tag_suppression: e.target.checked })}
          >
            Tag Suppression via Data Elements
          </Switch>
        </Section>

        {/* Consent Mapping */}
        <Section>
          <SectionHeading>Consent Purpose Mapping</SectionHeading>

          <Table>
            <Thead>
              <Tr>
                <Th>Fides Notice</Th>
                <Th>Adobe Purposes</Th>
                <Th>ECID Categories</Th>
                <Th>Actions</Th>
              </Tr>
            </Thead>
            <Tbody>
              <Tr>
                <Td>analytics</Td>
                <Td>
                  <TagGroup>
                    <Tag>collect</Tag>
                    <Tag>measure</Tag>
                  </TagGroup>
                </Td>
                <Td><Tag>aa</Tag></Td>
                <Td><Button size="sm">Edit</Button></Td>
              </Tr>
              <Tr>
                <Td>functional</Td>
                <Td><Tag>personalize</Tag></Td>
                <Td><Tag>target</Tag></Td>
                <Td><Button size="sm">Edit</Button></Td>
              </Tr>
              <Tr>
                <Td>advertising</Td>
                <Td><Tag>share</Tag></Td>
                <Td><Tag>aam</Tag></Td>
                <Td><Button size="sm">Edit</Button></Td>
              </Tr>
            </Tbody>
          </Table>

          <Button leftIcon={<AddIcon />} size="sm" mt={2}>
            Add Custom Mapping
          </Button>
        </Section>

        {/* OneTrust Migration */}
        <Section>
          <SectionHeading>OneTrust Migration</SectionHeading>

          <Text mb={2}>
            Map OneTrust categories to Fides notices for seamless migration
          </Text>

          <Table size="sm">
            <Thead>
              <Tr>
                <Th>OneTrust Category</Th>
                <Th>Fides Notice</Th>
              </Tr>
            </Thead>
            <Tbody>
              {Object.entries(config?.onetrust_mapping ?? {}).map(([otCat, fidesNotice]) => (
                <Tr key={otCat}>
                  <Td>
                    <Code>{otCat}</Code>
                  </Td>
                  <Td>
                    <Select
                      value={fidesNotice}
                      onChange={(e) => updateOneTrustMapping(otCat, e.target.value)}
                    >
                      <option value="necessary">Necessary</option>
                      <option value="functional">Functional</option>
                      <option value="analytics">Analytics</option>
                      <option value="advertising">Advertising</option>
                      <option value="data_sales_and_sharing">Data Sales & Sharing</option>
                    </Select>
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </Section>

        {/* Installation Instructions */}
        <Section>
          <SectionHeading>Installation</SectionHeading>

          <Text mb={2}>Add this script to your website after Fides.js:</Text>

          <Code display="block" p={4}>
            &lt;script&gt;Fides.adobe()&lt;/script&gt;
          </Code>

          <Button leftIcon={<CopyIcon />} size="sm" mt={2}>
            Copy Installation Code
          </Button>
        </Section>

        {/* Validation */}
        <Section>
          <SectionHeading>Validation</SectionHeading>

          <Button colorScheme="blue">
            Preview Consent Payload
          </Button>

          <Text fontSize="sm" color="gray.600" mt={2}>
            Test the consent mapping with sample data
          </Text>
        </Section>
      </CardBody>

      <CardFooter>
        <Button colorScheme="blue" onClick={saveConfig}>
          Save Configuration
        </Button>
      </CardFooter>
    </Card>
  );
};
```

#### 3.2 Backend API Endpoints

```python
# API endpoints for Adobe configuration
@router.post("/api/v1/destinations/adobe/{property_id}")
async def create_adobe_destination(
    property_id: str,
    config: AdobeDestinationConfigCreate,
    db: Session = Depends(get_db)
):
    """Create or update Adobe destination configuration"""
    # Validate property exists
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(404, "Property not found")

    # Create or update config
    adobe_config = db.query(AdobeDestinationConfig).filter(
        AdobeDestinationConfig.property_id == property_id
    ).first()

    if not adobe_config:
        adobe_config = AdobeDestinationConfig(property_id=property_id)

    adobe_config.enable_web_sdk = config.enable_web_sdk
    adobe_config.enable_ecid = config.enable_ecid
    adobe_config.enable_tag_suppression = config.enable_tag_suppression
    adobe_config.onetrust_mapping = config.onetrust_mapping
    adobe_config.web_sdk_mapping = config.web_sdk_mapping
    adobe_config.ecid_mapping = config.ecid_mapping

    db.add(adobe_config)
    db.commit()

    return adobe_config


@router.get("/api/v1/destinations/adobe/{property_id}")
async def get_adobe_destination(
    property_id: str,
    db: Session = Depends(get_db)
):
    """Get Adobe destination configuration"""
    config = db.query(AdobeDestinationConfig).filter(
        AdobeDestinationConfig.property_id == property_id
    ).first()

    if not config:
        raise HTTPException(404, "Adobe destination not configured")

    return config


@router.post("/api/v1/destinations/adobe/{property_id}/validate")
async def validate_adobe_config(
    property_id: str,
    sample_consent: dict,
    db: Session = Depends(get_db)
):
    """Preview Adobe consent payload with sample Fides consent"""
    config = db.query(AdobeDestinationConfig).filter(
        AdobeDestinationConfig.property_id == property_id
    ).first()

    if not config:
        raise HTTPException(404, "Adobe destination not configured")

    # Generate preview payloads
    web_sdk_payload = generate_web_sdk_payload(sample_consent, config.web_sdk_mapping)
    ecid_payload = generate_ecid_payload(sample_consent, config.ecid_mapping)

    return {
        "web_sdk": web_sdk_payload,
        "ecid": ecid_payload,
        "sample_consent": sample_consent
    }
```

---

## Data Elements & Rules

### Adobe Launch Data Elements

These should be documented for customers to create in their Adobe Launch property:

#### 1. FidesConsentObject

**Type:** Custom Code
**Purpose:** Expose full Fides consent object

```javascript
return window.Fides && window.Fides.consent || {};
```

#### 2. FidesActiveKeys

**Type:** Custom Code
**Purpose:** Comma-separated list of granted consents (OneTrust compatibility)

```javascript
var F = window.Fides;
if (!F || !F.consent) return "";

var keys = [];
for (var k in F.consent) {
  var v = F.consent[k];
  var allowed = (v === true) || (v === "opt_in") || (v === "acknowledge");
  if (allowed) keys.push(k);
}
return "," + keys.join(",") + ",";
```

#### 3. FidesConsentString

**Type:** Custom Code
**Purpose:** IAB TCF/GPP string

```javascript
return window.Fides && window.Fides.fides_string || "";
```

#### 4. Fides Analytics Consent

**Type:** Custom Code
**Purpose:** Boolean flag for analytics consent

```javascript
var consent = window.Fides && window.Fides.consent;
return consent && (consent.analytics === true || consent.analytics === "opt_in");
```

#### 5. Fides Advertising Consent

**Type:** Custom Code
**Purpose:** Boolean flag for advertising consent

```javascript
var consent = window.Fides && window.Fides.consent;
return consent && (consent.advertising === true || consent.advertising === "opt_in");
```

#### 6. Fides Functional Consent

**Type:** Custom Code
**Purpose:** Boolean flag for functional consent

```javascript
var consent = window.Fides && window.Fides.consent;
return consent && (consent.functional === true || consent.functional === "opt_in");
```

### Adobe Launch Rules

Customers should create these rules:

#### Rule 1: Set Adobe Web SDK Consent

**Event:** Custom Event
- Event Type: Custom Code
- Code:
  ```javascript
  return event.type === 'fides:ready' || event.type === 'fides:updated';
  ```

**Conditions:** None (always fire)

**Actions:** Adobe Experience Platform Web SDK → Update Consent
- Consent Standard: Adobe
- Consent Version: 2.0
- Custom Code:
  ```javascript
  var consent = window.Fides && window.Fides.consent || {};

  return {
    consent: [{
      standard: "Adobe",
      version: "2.0",
      value: {
        collect: { val: consent.analytics ? "y" : "n" },
        measure: { val: consent.analytics ? "y" : "n" },
        personalize: { val: consent.functional ? "y" : "n" },
        share: { val: consent.advertising ? "y" : "n" }
      }
    }],
    metadata: window.Fides && window.Fides.fides_string ? {
      iab: window.Fides.fides_string
    } : undefined
  };
  ```

#### Rule 2: Set ECID Opt-In (Legacy)

**Event:** Custom Event
- Event Type: Custom Code
- Code: Same as Rule 1

**Conditions:** Custom Code
```javascript
return typeof adobe !== 'undefined' && adobe.optIn;
```

**Actions:** Custom Code
```javascript
var consent = window.Fides && window.Fides.consent || {};
var mapping = {
  analytics: "aa",
  functional: "target",
  advertising: "aam"
};

for (var noticeKey in mapping) {
  var category = mapping[noticeKey];
  if (consent[noticeKey]) {
    adobe.optIn.approve(category, true);
  } else {
    adobe.optIn.deny(category, true);
  }
}

adobe.optIn.complete();
```

#### Rule 3: Fire Analytics (Conditional Example)

**Event:** Page Load → DOM Ready

**Conditions:** Custom Code
```javascript
return %Fides Analytics Consent% === true;
```

**Actions:** Adobe Analytics → Send Beacon

---

## Consent Mapping

### Default Mappings

Based on OneTrust parity requirements:

```typescript
// Fides Notice → Adobe Web SDK Purposes
const DEFAULT_WEBSDK_MAPPING = {
  analytics: ["collect", "measure"],
  functional: ["personalize"],
  advertising: ["share"],
  data_sales_and_sharing: ["share"],
  necessary: []  // Always allowed
};

// Fides Notice → ECID Categories
const DEFAULT_ECID_MAPPING = {
  analytics: ["aa"],
  functional: ["target"],
  advertising: ["aam"],
  data_sales_and_sharing: ["aam"],
  necessary: []
};

// OneTrust Category → Fides Notice (for migration)
const DEFAULT_ONETRUST_MAPPING = {
  "C0001": "necessary",
  "C0002": "functional",
  "C0003": "analytics",
  "C0004": "advertising",
  "C0005": "data_sales_and_sharing"
};
```

### Mapping Logic

The mapping resolution follows this priority:

1. **Admin UI Custom Mapping** (highest priority)
2. **Property-level Default**
3. **Global Default Mapping** (lowest priority)

### Multi-Key Mapping

Some Adobe purposes may require multiple Fides notices:

```typescript
// Example: "share" purpose granted if ANY of these notices are opted-in
{
  share: ["advertising", "data_sales_and_sharing", "targeted_advertising_gpp_us_state"]
}

// Resolution logic:
const hasShareConsent = ["advertising", "data_sales_and_sharing", "targeted_advertising_gpp_us_state"]
  .some(key => consent[key] === true || consent[key] === "opt_in");
```

---

## OneTrust Migration

### Migration Flow

```
┌─────────────────────────────────────────────────────────────┐
│  1. User visits website (has OptanonConsent cookie)         │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  2. FidesJS checks for OptanonConsent cookie                │
│     - Parses ActiveGroups (e.g., "C0001:1,C0003:1,C0004:0") │
│     - Loads ot_fides_mapping configuration                  │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Map OneTrust categories to Fides notices                │
│     C0001 (Necessary) → necessary: true                     │
│     C0002 (Functional) → (not in ActiveGroups) → false      │
│     C0003 (Analytics) → analytics: true                     │
│     C0004 (Advertising) → advertising: false                │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Initialize Fides with migrated consent                  │
│     - No banner shown (consent already collected)           │
│     - Save to Fides cookie with migration metadata          │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  5. Trigger FidesReady event with migrated consent          │
│     - Adobe rules fire with correct consent state           │
│     - User experience is seamless                           │
└─────────────────────────────────────────────────────────────┘
```

### Configuration Methods

#### Method 1: Global JavaScript Variable (Recommended)

```html
<script>
  // Define BEFORE Fides.js loads
  window.ot_fides_mapping = {
    "C0001": "necessary",
    "C0002": "functional",
    "C0003": "analytics",
    "C0004": "advertising",
    "C0005": "data_sales_and_sharing"
  };
</script>
<script src="https://privacy.example.com/fides.js"></script>
```

#### Method 2: Admin UI Configuration (Preferred)

Configure in Fides Admin UI → Adobe Destination → OneTrust Migration section.

The mapping is fetched from the backend and injected into Fides configuration:

```typescript
// Fides config includes oneTrustMigration
const fidesConfig = {
  // ...
  oneTrustMigration: {
    enabled: true,
    categoryMapping: {
      "C0001": "necessary",
      "C0002": "functional",
      "C0003": "analytics",
      "C0004": "advertising",
      "C0005": "data_sales_and_sharing"
    }
  }
};
```

### OptanonConsent Cookie Format

Example cookie value:
```
groups=C0001:1,C0002:0,C0003:1,C0004:1&datestamp=2025-11-05T10:30:00.000Z&version=6.33.0
```

Parsing logic:
- Split by `&` to get parameters
- `groups=` contains consent states
- Format: `CATEGORY:STATE` where STATE is `1` (opted-in) or `0` (opted-out)

### Edge Cases

1. **No OptanonConsent cookie**: Normal Fides flow (show banner)
2. **Invalid OptanonConsent format**: Log warning, fall back to normal flow
3. **Unknown OneTrust categories**: Ignore unmapped categories
4. **Conflicting Fides cookie exists**: Fides cookie takes precedence (user already interacted with Fides)

---

## Admin UI Requirements

### Adobe Destination Configuration Page

**Location:** Admin UI → Destinations → Adobe Experience Platform

**Components:**

1. **Integration Modes Section**
   - Checkbox: Enable Web SDK (Consent v2)
   - Checkbox: Enable ECID Opt-In Service (Legacy)
   - Checkbox: Enable Tag Suppression via Data Elements
   - Help text for each mode

2. **Consent Mapping Section**
   - Table with columns: Fides Notice | Adobe Purposes | ECID Categories | Actions
   - Each row is editable
   - Add/remove custom mappings
   - Reset to defaults button

3. **OneTrust Migration Section**
   - Enable/disable toggle
   - Table: OneTrust Category → Fides Notice mapping
   - Import mappings from CSV
   - Export current mappings

4. **Regional Defaults Section**
   - Region selector (US, EU, CA, etc.)
   - Default consent state per notice per region
   - Inherits from global property settings

5. **IAB TCF/GPP Section**
   - Toggle: Forward IAB strings to Adobe
   - Display current TCF/GPP configuration
   - Link to TCF configuration page

6. **Installation Instructions**
   - Copy-pasteable script tag
   - Link to full documentation
   - Sample Adobe Launch rule templates

7. **Validation & Testing**
   - Test with sample consent payload
   - Preview generated Adobe payloads
   - Validation status indicators

8. **Save & Deploy**
   - Save configuration
   - Deploy to environments
   - View deployment history

### Backend Models

```python
# Main Adobe destination configuration
class AdobeDestinationConfig(Base):
    __tablename__ = "adobe_destination_config"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    property_id = Column(String, ForeignKey("property.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Integration modes
    enable_web_sdk = Column(Boolean, default=True)
    enable_ecid = Column(Boolean, default=False)
    enable_tag_suppression = Column(Boolean, default=True)

    # Consent mappings (JSON)
    web_sdk_mapping = Column(JSON, default={...})  # Fides → Adobe purposes
    ecid_mapping = Column(JSON, default={...})      # Fides → ECID categories

    # OneTrust migration
    enable_onetrust_migration = Column(Boolean, default=False)
    onetrust_mapping = Column(JSON, default={...})  # OneTrust → Fides

    # IAB forwarding
    forward_iab_strings = Column(Boolean, default=True)

    # Regional defaults (JSON)
    regional_defaults = Column(JSON, default={})

    # Relationships
    property = relationship("Property", back_populates="adobe_destination")


# Consent mapping history (for auditing)
class AdobeConsentMappingHistory(Base):
    __tablename__ = "adobe_consent_mapping_history"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    config_id = Column(String, ForeignKey("adobe_destination_config.id"))
    changed_at = Column(DateTime, default=datetime.utcnow)
    changed_by = Column(String)  # User ID

    # What changed
    mapping_type = Column(String)  # "web_sdk" | "ecid" | "onetrust"
    old_mapping = Column(JSON)
    new_mapping = Column(JSON)
```

---

## Testing Strategy

### Unit Tests

**File:** `clients/fides-js/__tests__/integrations/adobe.test.ts`

```typescript
describe("Adobe Integration", () => {
  describe("Web SDK Mode", () => {
    it("should call alloy setConsent with correct payload", () => {
      // Test Web SDK consent setting
    });

    it("should map multiple Fides notices to single Adobe purpose", () => {
      // Test multi-key mapping
    });

    it("should include IAB string in metadata", () => {
      // Test TCF/GPP forwarding
    });
  });

  describe("ECID Mode", () => {
    it("should call adobe.optIn.approve for granted consent", () => {
      // Test ECID approve
    });

    it("should call adobe.optIn.deny for denied consent", () => {
      // Test ECID deny
    });

    it("should call adobe.optIn.complete after all categories", () => {
      // Test completion signal
    });
  });

  describe("OneTrust Migration", () => {
    it("should parse OptanonConsent cookie correctly", () => {
      // Test cookie parsing
    });

    it("should map OneTrust categories to Fides notices", () => {
      // Test category mapping
    });

    it("should use ot_fides_mapping if available", () => {
      // Test custom mapping
    });

    it("should handle invalid OptanonConsent gracefully", () => {
      // Test error handling
    });
  });

  describe("Event Dispatching", () => {
    it("should dispatch fides:ready event", () => {
      // Test custom event
    });

    it("should call _satellite.track if available", () => {
      // Test Adobe Launch integration
    });
  });
});
```

### Integration Tests

**File:** `clients/privacy-center/cypress/e2e/fides-js/adobe-integration.cy.ts`

```typescript
describe("Adobe Experience Platform Integration", () => {
  beforeEach(() => {
    // Mock Adobe SDKs
    cy.window().then((win) => {
      // Mock alloy
      win.alloy = cy.stub().as("alloy");

      // Mock adobe.optIn
      win.adobe = {
        optIn: {
          approve: cy.stub().as("optInApprove"),
          deny: cy.stub().as("optInDeny"),
          complete: cy.stub().as("optInComplete")
        }
      };

      // Mock _satellite
      win._satellite = {
        track: cy.stub().as("satelliteTrack")
      };
    });
  });

  it("should initialize Adobe integration on page load", () => {
    cy.visit("/");
    cy.get("@alloy").should("have.been.called");
  });

  it("should update Adobe consent when user opts in", () => {
    cy.visit("/");

    // Wait for Fides banner
    cy.get("#fides-banner").should("be.visible");

    // Click opt-in
    cy.get("button").contains("Accept All").click();

    // Verify Adobe consent updated
    cy.get("@alloy").should("have.been.calledWith", "setConsent",
      Cypress.sinon.match({
        consent: Cypress.sinon.match.array
      })
    );
  });

  it("should migrate OneTrust consent", () => {
    // Set OptanonConsent cookie
    cy.setCookie("OptanonConsent", encodeURIComponent(
      "groups=C0001:1,C0003:1,C0004:0&datestamp=2025-11-05T10:00:00Z"
    ));

    cy.visit("/");

    // Verify no banner shown (already consented)
    cy.get("#fides-banner").should("not.exist");

    // Verify consent state matches OneTrust
    cy.window().then((win) => {
      expect(win.Fides.consent.necessary).to.be.true;
      expect(win.Fides.consent.analytics).to.be.true;
      expect(win.Fides.consent.advertising).to.be.false;
    });
  });
});
```

### Manual Testing Checklist

#### Setup
- [ ] Create Adobe Launch property in Adobe Experience Cloud
- [ ] Add FidesJS script to test page
- [ ] Add `Fides.adobe()` call after FidesJS
- [ ] Add Adobe Launch library to test page
- [ ] Install Adobe Experience Platform Debugger extension

#### Web SDK Mode
- [ ] Verify alloy("setConsent") called on FidesReady
- [ ] Check Adobe Debugger shows consent status
- [ ] Verify consent purposes match Fides notices
- [ ] Test consent update (opt-in → opt-out)
- [ ] Verify IAB string included (if TCF/GPP enabled)

#### ECID Mode
- [ ] Verify adobe.optIn.approve() called for granted consent
- [ ] Verify adobe.optIn.deny() called for denied consent
- [ ] Check ECID categories match configuration
- [ ] Test with AppMeasurement (aa category)
- [ ] Test with Adobe Target (target category)
- [ ] Test with Audience Manager (aam category)

#### Tag Suppression Mode
- [ ] Verify data elements populate correctly
- [ ] Test rule conditions based on data elements
- [ ] Verify tags fire only with consent
- [ ] Verify tags blocked without consent

#### OneTrust Migration
- [ ] Set OptanonConsent cookie with known values
- [ ] Verify Fides reads OptanonConsent on first load
- [ ] Verify correct mapping to Fides notices
- [ ] Verify no banner shown (consent already collected)
- [ ] Verify Fides cookie created with migration metadata

#### Admin UI
- [ ] Configure Adobe destination
- [ ] Edit consent mappings
- [ ] Configure OneTrust migration
- [ ] Test validation/preview
- [ ] Save and verify configuration persists

#### Browser Compatibility
- [ ] Chrome
- [ ] Firefox
- [ ] Safari
- [ ] Edge
- [ ] Mobile Safari
- [ ] Chrome Mobile

---

## Success Criteria

### Functional Requirements

- ✅ All three integration modes work correctly
- ✅ Consent syncs between Fides and Adobe in real-time
- ✅ OneTrust migration works seamlessly (no re-consent)
- ✅ IAB TCF/GPP strings forwarded to Adobe
- ✅ Admin UI allows complete configuration
- ✅ Default mappings match OneTrust parity
- ✅ Regional defaults work correctly

### Non-Functional Requirements

- ✅ Zero console errors in production
- ✅ < 50ms latency for consent updates
- ✅ Compatible with Adobe Web SDK 2.0+
- ✅ Compatible with ECID Service 4.0+
- ✅ Works in all major browsers
- ✅ No memory leaks

### Documentation Requirements

- ✅ Complete installation guide
- ✅ Adobe Launch rule templates documented
- ✅ OneTrust migration guide
- ✅ API reference documentation
- ✅ Troubleshooting guide
- ✅ Video tutorial (nice to have)

### Customer Success Metrics

- ✅ 5+ OneTrust customers successfully migrate in first month
- ✅ < 5 support tickets per month after launch
- ✅ Positive customer feedback (NPS > 8)
- ✅ Zero critical bugs in first 30 days

---

## Timeline

### Week 1-3: Core Integration
- **Week 1:** FidesJS Adobe integration module (Web SDK + ECID)
- **Week 2:** Event dispatching, data elements, testing
- **Week 3:** Code review, bug fixes, polish

**Deliverable:** Working `Fides.adobe()` integration for all three modes

### Week 3-4: OneTrust Migration
- **Week 3:** OneTrust migration module
- **Week 4:** Integration with Fides init, testing

**Deliverable:** Seamless OneTrust → Fides migration

### Week 4-5: Admin UI
- **Week 4:** Backend API and models
- **Week 5:** Frontend UI components

**Deliverable:** Complete Admin UI for Adobe configuration

### Week 5-6: Documentation
- **Week 5:** User-facing documentation
- **Week 6:** Developer docs, API reference, tutorials

**Deliverable:** Complete documentation suite

### Week 6-7: Testing & QA
- **Week 6:** Integration testing, manual testing
- **Week 7:** Bug fixes, regression testing

**Deliverable:** Production-ready, tested integration

### Week 7-8: Launch Prep
- **Week 7:** Customer preview, feedback incorporation
- **Week 8:** Final polish, launch preparation

**Deliverable:** Launch-ready Adobe integration

**Total: 8 weeks**

---

## Dependencies

### External Dependencies
- Adobe Experience Platform Launch account (for testing)
- Adobe Web SDK documentation access
- ECID Service documentation access
- OneTrust documentation (for parity verification)

### Internal Dependencies
- FidesJS SDK v2.6+ (events: FidesReady, FidesUpdated)
- Fides Admin UI destination framework
- Backend API for destination configuration
- Existing OneTrust migration support (extend for Adobe)

### Team Dependencies
- Frontend Engineer (FidesJS integration)
- Backend Engineer (API & Admin UI)
- QA Engineer (testing)
- Technical Writer (documentation)
- Product Manager (customer validation)

---

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Adobe API changes between versions | High | Low | Support multiple Adobe SDK versions, version detection |
| OneTrust migration edge cases | Medium | Medium | Extensive testing with real OneTrust cookies, fallback to normal flow |
| Complex customer configurations | Medium | High | Provide clear documentation, validation tools, support |
| Browser compatibility issues | Medium | Low | Test all browsers, use standard APIs, polyfills if needed |
| Customer confusion during migration | High | Medium | Clear migration guide, video tutorials, dedicated support |
| Performance impact on page load | Medium | Low | Async operations, benchmark, optimize |

---

## Out of Scope (Future Phases)

The following are explicitly **out of scope** for this implementation:

1. **Server-Side Adobe APIs** - Only client-side (Launch) integration
2. **Mobile SDK Integration** - Web only for now
3. **Adobe Target/AAM Advanced Configuration** - Basic consent gating only
4. **Automated Launch Property Setup** - Manual configuration required
5. **Adobe Analytics Custom Dimensions** - Standard implementation only
6. **Other Adobe Products** - Focus on Analytics, Target, AAM only
7. **Real-Time CDP Integration** - Future enhancement

---

## References

### Adobe Documentation
- [Adobe Consent Standard v2](https://experienceleague.adobe.com/docs/experience-platform/edge/consent/supporting-consent.html)
- [ECID Opt-In Service](https://experienceleague.adobe.com/docs/id-service/using/implementation/opt-in-service/getting-started.html)
- [Adobe Launch Implementation](https://experienceleague.adobe.com/docs/experience-platform/tags/home.html)

### OneTrust Documentation
- [OneTrust Adobe Launch Integration](https://community.cookiepro.com/s/article/UUID-5f01d9ba-2e38-d018-b1a0-f41bd60f64c3)
- [OneTrust Adobe Experience Cloud Guide](https://community.cookiepro.com/s/article/UUID-6a48d849-59ee-4494-b9f1-0f3baa51e6f4)

### Fides Documentation
- [Fides GTM Integration](https://docs.ethyca.com/consent-management/configure-gtm) (reference for similar integration)
- [OneTrust Migration](https://docs.ethyca.com/consent-management/onetrust-migration)
- [Fides SDK Events](https://docs.ethyca.com/fides-sdk/events)

---

## Appendix A: Code Examples

### Complete Adobe Integration Example

```html
<!DOCTYPE html>
<html>
<head>
  <!-- 1. Load Fides JS -->
  <script src="https://privacy.example.com/fides.js"></script>

  <!-- 2. Configure OneTrust migration (optional) -->
  <script>
    window.ot_fides_mapping = {
      "C0001": "necessary",
      "C0002": "functional",
      "C0003": "analytics",
      "C0004": "advertising"
    };
  </script>

  <!-- 3. Enable Adobe integration -->
  <script>
    Fides.adobe({
      enableWebSDK: true,
      enableECID: false,  // Only if using legacy AppMeasurement
      webSDKMapping: {
        collect: ['analytics'],
        measure: ['analytics'],
        personalize: ['functional'],
        share: ['advertising', 'data_sales_and_sharing']
      }
    });
  </script>

  <!-- 4. Load Adobe Launch library -->
  <script src="https://assets.adobedtm.com/launch-XXXXX.min.js"></script>
</head>
<body>
  <!-- Your content -->
</body>
</html>
```

---

## Appendix B: Troubleshooting Guide

### Issue: Adobe consent not updating

**Symptoms:** Tags fire without consent

**Causes:**
1. `Fides.adobe()` not called
2. Adobe Launch rules not configured
3. Event names mismatch

**Solutions:**
1. Verify `Fides.adobe()` in page source
2. Check Adobe Launch rules in debugger
3. Check event names (should be `fides:ready`, `fides:updated`)

### Issue: OneTrust migration not working

**Symptoms:** Banner shows despite OptanonConsent cookie

**Causes:**
1. `ot_fides_mapping` not defined
2. OptanonConsent cookie invalid
3. Fides cookie already exists

**Solutions:**
1. Define `ot_fides_mapping` before Fides.js
2. Check OptanonConsent format in DevTools
3. Clear Fides cookie and retry

---

**Document Status:** Ready for Review
**Next Steps:** Team review → Begin implementation
