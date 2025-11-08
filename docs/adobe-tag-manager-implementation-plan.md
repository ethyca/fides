# Adobe Tag Manager (Adobe Launch) Integration Implementation Plan

**Document Version:** 1.0
**Date:** November 5, 2025
**Status:** Reference Document (Comprehensive Scope)
**Current Implementation:** See [PRD-Focused Implementation](./adobe-experience-platform-integration-prd.md) for active Phase 1 work

---

> **📌 NOTE:** This document provides comprehensive Adobe integration architecture and future enhancements. For the **current focused implementation** (OneTrust parity, migration, and PRD requirements), see the [Adobe Experience Platform Integration PRD document](./adobe-experience-platform-integration-prd.md).

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Background: Current GTM Integration](#background-current-gtm-integration)
3. [Architectural Analysis](#architectural-analysis)
4. [Adobe Tag Manager Overview](#adobe-tag-manager-overview)
5. [Proposed Architecture Improvements](#proposed-architecture-improvements)
6. [Implementation Plan](#implementation-plan)
7. [Testing Strategy](#testing-strategy)
8. [Documentation Requirements](#documentation-requirements)
9. [Timeline & Resources](#timeline--resources)

---

## Document Scope & Relationship

### This Document (Comprehensive Plan)
This document provides:
- **Broad architectural analysis** of all tag manager integrations
- **General Adobe integration patterns** for future enhancements
- **Long-term vision** for tag manager abstraction framework
- **Reference material** for understanding integration landscape

**Use this document for:**
- Understanding overall architecture
- Planning future enhancements beyond Phase 1
- Architectural decision-making
- Long-term roadmap planning

### PRD Implementation Document
The **[Adobe Experience Platform Integration PRD](./adobe-experience-platform-integration-prd.md)** document provides:
- **Specific requirements** from PRD 221515.pdf
- **OneTrust parity** implementation details
- **Three integration modes** (Web SDK, ECID, Tag Suppression)
- **OneTrust migration** implementation
- **8-week timeline** with concrete deliverables

**Use that document for:**
- Active implementation work (Phase 1)
- Sprint planning and task breakdown
- Customer requirements and success criteria
- OneTrust migration details

---

## Executive Summary

This document outlines the **comprehensive vision** for Adobe Tag Manager (Adobe Launch) integration with Fides consent management. It provides architectural analysis, identifies improvement opportunities, and describes potential future enhancements beyond the initial PRD-focused implementation.

**Key Findings:**
- Current integrations lack abstraction layer - each is implemented independently
- Significant code duplication in event listening and consent mapping patterns
- Opportunity to create a reusable Tag Manager Integration Framework (future phase)
- Adobe Launch has a different architecture than GTM that requires careful consideration

**Recommended Approach:**
1. **Phase 1 (Current):** Implement PRD requirements without abstraction (see [PRD document](./adobe-experience-platform-integration-prd.md))
2. **Phase 2 (Future):** Extract shared utilities after patterns become clear
3. **Phase 3 (Future):** Consider abstraction framework when 3+ tag managers exist

---

## Background: Current GTM Integration

### Overview

Fides currently has a mature Google Tag Manager integration that synchronizes consent preferences with GTM's Consent Mode v2. The integration is production-ready and widely used.

### GTM Integration Components

#### 1. **Fides.js GTM Module** (`clients/fides-js/src/integrations/gtm.ts`)

**Purpose:** Core JavaScript integration that pushes Fides events to GTM's dataLayer

**Key Features:**
- Listens to Fides events (FidesReady, FidesUpdated, etc.)
- Pushes consent state to `window.dataLayer`
- Configurable consent value formats (boolean vs consent mechanism strings)
- Handles non-applicable notices

**API:**
```javascript
Fides.gtm(options?: {
  non_applicable_flag_mode?: "omit" | "include";
  flag_type?: "boolean" | "consent_mechanism";
})
```

**Events Published:**
- `FidesInitialized` (deprecated but still sent)
- `FidesConsentLoaded`
- `FidesReady`
- `FidesUpdating`
- `FidesUpdated`
- `FidesUIChanged`
- `FidesUIShown`
- `FidesModalClosed`
- (NOT `FidesInitializing`)

**Data Structure:**
```typescript
{
  event: "FidesUpdated",
  Fides: {
    consent: {
      analytics: true,
      marketing: false,
      data_sales_and_sharing: false
    },
    extraDetails: { ... },
    fides_string: "...",
    timestamp: 1234567890
  }
}
```

#### 2. **GTM Custom Template** (`fidesplus/clients/fides-gtm/template.tpl`)

**Purpose:** GTM Community Template that maps Fides consent to GTM Consent Mode

**Consent Mapping:**
```javascript
{
  ad_storage: ["marketing", "data_sales_and_sharing", ...],
  ad_user_data: ["marketing", "data_sales_and_sharing", ...],
  ad_personalization: ["marketing", "data_sales_and_sharing", ...],
  analytics_storage: ["analytics"],
  functionality_storage: ["functional"],
  personalization_storage: ["functional"],
  security_storage: ["essential"]
}
```

**Features:**
- Default consent states per consent type
- Regional consent defaults (GDPR, CCPA, etc.)
- Wait timeout (1000ms default) for Fides.js initialization
- Optional Fides.js script injection
- Listens for both `FidesInitialized` and `FidesUpdating` events

#### 3. **Sample Application Integration**

**Environment Variable:**
```bash
FIDES_SAMPLE_APP__GOOGLE_TAG_MANAGER_CONTAINER_ID=GTM-ABCD123
```

**Implementation Pattern:**
```html
<script src="https://privacy.example.com/fides.js"></script>
<script>Fides.gtm()</script>
<!-- GTM script follows -->
```

#### 4. **Admin UI Support**

- Copy-pasteable script tags
- Installation guidance modal
- Property-specific configuration

#### 5. **Data Discovery & Detection**

- Automatic detection of GTM assets (`www.googletagmanager.com`)
- System categorization in Action Center
- Compliance monitoring

### GTM Integration Benefits

1. **Privacy-Compliant Tag Management** - Ensures tags respect user consent
2. **Google Consent Mode v2 Support** - Full integration with Google's framework
3. **Real-time Synchronization** - Immediate consent propagation
4. **Regional Compliance** - Region-specific defaults (GDPR, CCPA, etc.)
5. **Easy Integration** - Simple one-line script tag
6. **Asset Discovery** - Automatic GTM resource detection
7. **Flexible Configuration** - Multiple consent value formats

### GTM Architecture Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                         Website                              │
│                                                              │
│  ┌────────────┐        ┌──────────────┐                     │
│  │ Fides.js   │───────▶│ Fides.gtm()  │                     │
│  │            │        │              │                     │
│  │ - Events   │        │ - Event      │                     │
│  │ - Consent  │        │   Listener   │                     │
│  └────────────┘        │ - Consent    │                     │
│                        │   Mapper     │                     │
│                        └──────┬───────┘                     │
│                               │                              │
│                               ▼                              │
│                        ┌──────────────┐                     │
│                        │ dataLayer[]  │                     │
│                        └──────┬───────┘                     │
│                               │                              │
│                               ▼                              │
│  ┌─────────────────────────────────────────────────┐        │
│  │           Google Tag Manager Container          │        │
│  │                                                  │        │
│  │  ┌──────────────────────────────────────────┐  │        │
│  │  │     Ethyca CMP Custom Template          │  │        │
│  │  │                                          │  │        │
│  │  │  - Listens for FidesUpdated events      │  │        │
│  │  │  - Maps Fides consent → GTM consent     │  │        │
│  │  │  - Calls setDefaultConsentState()       │  │        │
│  │  │  - Calls updateConsentState()           │  │        │
│  │  └──────────────────────────────────────────┘  │        │
│  │                                                  │        │
│  │  ┌──────────────────────────────────────────┐  │        │
│  │  │   GTM Consent Mode State                │  │        │
│  │  │                                          │  │        │
│  │  │  - ad_storage: granted/denied           │  │        │
│  │  │  - analytics_storage: granted/denied    │  │        │
│  │  │  - ad_personalization: granted/denied   │  │        │
│  │  └──────────────────────────────────────────┘  │        │
│  │                                                  │        │
│  │  ┌──────────────────────────────────────────┐  │        │
│  │  │   Tags (Triggers & Conditions)          │  │        │
│  │  │                                          │  │        │
│  │  │  - Google Analytics (blocked if denied) │  │        │
│  │  │  - Google Ads (blocked if denied)       │  │        │
│  │  │  - Facebook Pixel (blocked if denied)   │  │        │
│  │  └──────────────────────────────────────────┘  │        │
│  └─────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### Changelog History

- **v2.0** (#6090) - Fixed GTM integration to properly handle duplicate notice keys
- **v1.5** (#5917) - Added support for new options for `Fides.gtm()` method
- **v1.4** (#5821) - Updated FidesJS to push all `FidesEvent` types to GTM
- **v1.3** (#5859) - Added high-precision timestamp to all FidesEvents
- **v1.2** (#4847) - Hydrated GTM dataLayer to match supported FidesEvent properties
- **v1.0** (#3411, #2949) - Initial GTM integration and lifecycle events

---

## Architectural Analysis

### Current Integration Pattern

All integrations (GTM, Shopify, Meta, BlueConic) follow this pattern:

1. **Individual Files:** Each integration lives in `clients/fides-js/src/integrations/{name}.ts`
2. **Exported Function:** Each exports a setup function (e.g., `export const gtm = (options?) => {...}`)
3. **Direct Assignment:** Functions are imported and assigned to `window.Fides` object:
   ```typescript
   // In init-utils.ts
   import { gtm } from "../integrations/gtm";
   import { shopify } from "../integrations/shopify";

   const coreFides = {
     // ...
     gtm,
     shopify,
     // ...
   };
   ```
4. **Event Listening:** Each integration independently sets up event listeners
5. **Consent Mapping:** Each has its own CONSENT_MAP logic

### Code Structure

```
clients/fides-js/src/
├── integrations/
│   ├── gtm.ts           # Google Tag Manager
│   ├── shopify.ts       # Shopify Customer Privacy API
│   ├── meta.ts          # Meta/Facebook Pixel
│   └── blueconic.ts     # BlueConic CDP
├── lib/
│   ├── init-utils.ts    # Where integrations are wired up
│   └── events.ts        # Fides event system
└── docs/
    └── fides.ts         # TypeScript definitions
```

### Architectural Strengths

1. ✅ **Simple & Direct:** No over-engineering, easy to understand
2. ✅ **Independent:** Each integration is self-contained
3. ✅ **Flexible:** Each can have unique options and behavior
4. ✅ **Testable:** Each can be tested in isolation

### Architectural Weaknesses

1. ❌ **Code Duplication:** Event listener setup repeated in each integration
2. ❌ **Consent Mapping Duplication:** Similar mapping patterns across integrations
3. ❌ **No Shared Utilities:** Common functionality reimplemented
4. ❌ **No Standard Interface:** Each integration has different structure
5. ❌ **Limited Extensibility:** Adding new integrations requires understanding all patterns
6. ❌ **Type Safety Gaps:** Integration options not standardized

### Integration Comparison

| Feature | GTM | Shopify | Meta | BlueConic |
|---------|-----|---------|------|-----------|
| **Primary API** | dataLayer.push() | customerPrivacy.setTrackingConsent() | fbq() calls | CDP API |
| **Events Used** | 8 Fides events | FidesReady, FidesUpdating | Manual sync | Event-based |
| **Consent Format** | Boolean flags | Boolean flags | Boolean + strings | Custom |
| **Mapping Logic** | Multi-key mapping | Multi-key mapping | Direct options | Custom |
| **Options Interface** | 2 options | 1 option | 2 options | Varies |
| **Initialization** | Immediate | Requires Shopify API | Immediate | Custom |

### Common Patterns Identified

All integrations share these patterns:

1. **Event Subscription:**
   ```typescript
   window.addEventListener("FidesReady", (event) => { ... });
   window.addEventListener("FidesUpdating", (event) => { ... });
   ```

2. **Consent Mapping:**
   ```typescript
   const CONSENT_MAP = {
     target_consent_type: ["fides_notice_key_1", "fides_notice_key_2"],
     // ...
   };
   ```

3. **Boolean Resolution:**
   ```typescript
   const hasTrue = noticeKeys.some(key => consent[key] === true);
   const hasFalse = noticeKeys.some(key => consent[key] === false);
   ```

4. **Default Fallbacks:**
   ```typescript
   if (mappedValue === undefined) {
     mappedValue = defaultValue;
   }
   ```

---

## Adobe Tag Manager Overview

### Adobe Experience Platform Launch (Adobe Launch)

Adobe Tag Manager, officially called **Adobe Experience Platform Launch** (or simply **Adobe Launch**), is Adobe's tag management system. It's the successor to Adobe Dynamic Tag Manager (DTM).

### Key Differences from GTM

| Feature | Google Tag Manager | Adobe Launch |
|---------|-------------------|--------------|
| **Data Layer** | `window.dataLayer` array | Custom data elements & _satellite object |
| **Event System** | Push events to array | Direct event dispatch via `_satellite.track()` |
| **Consent Mode** | Native Consent Mode API | Custom consent extensions |
| **Rule Triggers** | Built-in GTM triggers | More flexible rule conditions |
| **Extension Model** | Community templates (sandboxed) | Full extensions with custom code |
| **Deployment** | Single container script | Library + embed code |
| **Configuration** | GTM UI only | Property + Environment configs |

### Adobe Launch Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Website                              │
│                                                              │
│  ┌────────────┐        ┌──────────────┐                     │
│  │ Fides.js   │───────▶│Fides.adobe() │                     │
│  │            │        │              │                     │
│  │ - Events   │        │ - Event      │                     │
│  │ - Consent  │        │   Dispatch   │                     │
│  └────────────┘        │ - Data       │                     │
│                        │   Elements   │                     │
│                        └──────┬───────┘                     │
│                               │                              │
│                               ▼                              │
│                     ┌────────────────────┐                  │
│                     │  _satellite.track  │                  │
│                     │  Custom Events     │                  │
│                     │  Data Elements     │                  │
│                     └──────┬─────────────┘                  │
│                            │                                 │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────┐        │
│  │         Adobe Launch Library                    │        │
│  │                                                  │        │
│  │  ┌──────────────────────────────────────────┐  │        │
│  │  │    Rules Engine                         │  │        │
│  │  │                                          │  │        │
│  │  │  - Event triggers (Fides events)        │  │        │
│  │  │  - Conditions (consent checks)          │  │        │
│  │  │  - Actions (fire tags or block)         │  │        │
│  │  └──────────────────────────────────────────┘  │        │
│  │                                                  │        │
│  │  ┌──────────────────────────────────────────┐  │        │
│  │  │    Data Elements                        │  │        │
│  │  │                                          │  │        │
│  │  │  - Fides.consent.analytics             │  │        │
│  │  │  - Fides.consent.marketing             │  │        │
│  │  │  - Fides.consent.data_sales            │  │        │
│  │  └──────────────────────────────────────────┘  │        │
│  │                                                  │        │
│  │  ┌──────────────────────────────────────────┐  │        │
│  │  │    Extensions                           │  │        │
│  │  │                                          │  │        │
│  │  │  - Adobe Analytics                      │  │        │
│  │  │  - Adobe Target                         │  │        │
│  │  │  - Google Analytics                     │  │        │
│  │  │  - Custom Extensions                    │  │        │
│  │  └──────────────────────────────────────────┘  │        │
│  └─────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### Adobe Launch API Surface

Unlike GTM's simple `dataLayer.push()`, Adobe Launch uses:

1. **_satellite Object:**
   ```javascript
   _satellite.track('eventName', { data });
   _satellite.setVar('variableName', value);
   _satellite.getVar('variableName');
   ```

2. **Custom Events:**
   ```javascript
   _satellite.track('fides-consent-updated', {
     consent: { analytics: true, marketing: false },
     timestamp: Date.now()
   });
   ```

3. **Data Elements:**
   - Accessible via `%Data Element Name%` in UI
   - Accessible via `_satellite.getVar('data-element-name')` in code

4. **No Native Consent Mode:**
   - Adobe doesn't have a GTM-like Consent Mode
   - Consent is handled via custom rules and conditions
   - Each tag needs explicit consent conditions

### Integration Approach for Adobe Launch

**Option 1: Event-Based (Recommended)**
- Dispatch custom Adobe events when Fides events fire
- Use Launch rules to listen for these events
- Set data elements from Fides consent object
- Use data elements in rule conditions

**Option 2: Direct Object Access**
- Expose Fides consent on `window.Fides.consent`
- Configure Launch data elements to read from window.Fides
- Rules check data elements before firing tags

**Option 3: Hybrid**
- Use events for real-time updates
- Use direct access for synchronous checks
- Best of both worlds

---

## Proposed Architecture Improvements

### Recommendation: Hybrid Approach

**For Adobe implementation:** Use current pattern (no abstraction) initially
**For future integrations:** Consider abstraction layer after 3+ tag manager integrations exist

### Rationale

1. **Current State:** Only 2 tag managers (GTM + planned Adobe)
2. **Different Paradigms:** GTM and Adobe have fundamentally different architectures
3. **Premature Abstraction:** Creating abstraction layer for 2 cases is premature
4. **Simple Solution:** Follow existing GTM pattern for Adobe integration
5. **Future Flexibility:** Wait for clear patterns to emerge before abstracting

### When to Introduce Abstraction

Create a Tag Manager Integration Framework when:
- ✅ 3+ tag manager integrations exist
- ✅ Clear common patterns emerge
- ✅ Integration requests increase
- ✅ Maintenance burden of duplication grows

### Potential Future Abstraction

*For reference when the time comes:*

```typescript
// clients/fides-js/src/integrations/core/tag-manager-base.ts

export interface TagManagerIntegration {
  name: string;
  init(options?: any): void;
  pushConsent(consent: NoticeConsent): void;
  pushEvent(eventType: FidesEventType, detail: FidesEventDetail): void;
  isAvailable(): boolean;
}

export interface ConsentMapping {
  [targetKey: string]: string[];  // target → [fides notice keys]
}

export abstract class BaseTagManagerIntegration implements TagManagerIntegration {
  abstract name: string;
  abstract consentMap: ConsentMapping;

  protected listenToFidesEvents(eventTypes: FidesEventType[]) {
    eventTypes.forEach(type => {
      window.addEventListener(type, (event) => {
        this.pushEvent(type, event.detail);
      });
    });
  }

  protected mapConsent(fidesConsent: NoticeConsent): Record<string, boolean> {
    const result: Record<string, boolean> = {};

    for (const [targetKey, sourceKeys] of Object.entries(this.consentMap)) {
      const hasTrue = sourceKeys.some(key => fidesConsent[key] === true);
      const hasFalse = sourceKeys.some(key => fidesConsent[key] === false);

      if (hasTrue) {
        result[targetKey] = true;
      } else if (hasFalse) {
        result[targetKey] = false;
      }
    }

    return result;
  }

  abstract init(options?: any): void;
  abstract pushConsent(consent: NoticeConsent): void;
  abstract pushEvent(eventType: FidesEventType, detail: FidesEventDetail): void;
  abstract isAvailable(): boolean;
}
```

### Recommended Improvements for Current Architecture

Even without full abstraction, we should:

1. **Extract Common Utilities** (Phase 1 - Immediate)
   ```typescript
   // clients/fides-js/src/integrations/utils/consent-mapper.ts
   export function mapConsentByKeys(
     fidesConsent: NoticeConsent,
     mapping: Record<string, string[]>
   ): Record<string, boolean> {
     // Shared logic for consent mapping
   }
   ```

2. **Standardize Event Subscription** (Phase 1 - Immediate)
   ```typescript
   // clients/fides-js/src/integrations/utils/event-subscriber.ts
   export function subscribeToFidesEvents(
     events: FidesEventType[],
     handler: (event: FidesEventDetail) => void
   ): () => void {
     // Returns cleanup function
   }
   ```

3. **Common TypeScript Types** (Phase 1 - Immediate)
   ```typescript
   // clients/fides-js/src/integrations/types.ts
   export interface ConsentMapping {
     [targetKey: string]: string[];
   }

   export interface IntegrationOptions {
     // Common options across integrations
   }
   ```

4. **Documentation Template** (Phase 2 - Near-term)
   - Standard integration documentation format
   - Common examples and patterns
   - Troubleshooting guide template

---

## Implementation Plan

### Phase 1: Adobe Launch Core Integration (Week 1-2)

**Goal:** Create working `Fides.adobe()` integration following GTM pattern

#### 1.1 Create Integration File

**File:** `clients/fides-js/src/integrations/adobe.ts`

```typescript
import { FidesEvent, FidesEventType } from "../docs";
import { NoticeConsent } from "../lib/consent-types";
import { FidesEventDetail } from "../lib/events";

declare global {
  interface Window {
    _satellite?: {
      track: (event: string, detail?: any) => void;
      setVar: (name: string, value: any) => void;
      getVar: (name: string) => any;
      logger: {
        log: (message: string) => void;
      };
    };
  }
}

export interface AdobeOptions {
  /**
   * Event prefix for Adobe Launch events
   * Default: "fides"
   */
  eventPrefix?: string;

  /**
   * Whether to set data elements in addition to dispatching events
   * Default: true
   */
  setDataElements?: boolean;

  /**
   * Custom consent mapping (advanced users)
   */
  consentMapping?: Record<string, string[]>;
}

/**
 * Default mapping of Fides notice keys to Adobe consent categories
 */
const DEFAULT_CONSENT_MAP: Record<string, string[]> = {
  analytics: ["analytics"],
  marketing: [
    "marketing",
    "data_sales_and_sharing",
    "data_sales_sharing_gpp_us_state",
    "data_sharing_gpp_us_state",
    "data_sales_gpp_us_state",
    "targeted_advertising_gpp_us_state",
  ],
  functional: ["functional"],
  essential: ["essential"],
};

/**
 * Map Fides consent to Adobe consent categories
 */
function mapConsentForAdobe(
  fidesConsent: NoticeConsent,
  mapping: Record<string, string[]>
): Record<string, boolean> {
  const result: Record<string, boolean> = {};

  for (const [category, noticeKeys] of Object.entries(mapping)) {
    const hasTrue = noticeKeys.some(key => fidesConsent[key] === true);
    const hasFalse = noticeKeys.some(key => fidesConsent[key] === false);

    if (hasTrue) {
      result[category] = true;
    } else if (hasFalse) {
      result[category] = false;
    }
  }

  return result;
}

/**
 * Push Fides event to Adobe Launch
 */
function dispatchAdobeEvent(
  eventName: string,
  detail: FidesEventDetail,
  options: AdobeOptions
) {
  if (!window._satellite) {
    // eslint-disable-next-line no-console
    console.warn("Adobe Launch (_satellite) is not available");
    return;
  }

  const prefix = options.eventPrefix || "fides";
  const fullEventName = `${prefix}:${eventName}`;

  // Prepare Adobe-friendly payload
  const adobePayload = {
    consent: mapConsentForAdobe(
      detail.consent,
      options.consentMapping || DEFAULT_CONSENT_MAP
    ),
    timestamp: detail.timestamp,
    extraDetails: detail.extraDetails,
  };

  // Dispatch the event
  window._satellite.track(fullEventName, adobePayload);

  // Optionally set data elements for synchronous access
  if (options.setDataElements !== false) {
    window._satellite.setVar("fides-consent", adobePayload.consent);
    window._satellite.setVar("fides-timestamp", adobePayload.timestamp);
  }
}

/**
 * Call Fides.adobe() to configure the Fides <> Adobe Launch integration.
 * User consent choices will automatically be pushed to Adobe Launch as
 * custom events and data elements.
 */
export const adobe = (options: AdobeOptions = {}) => {
  // Events to dispatch to Adobe Launch
  const fidesEvents: Record<FidesEventType, boolean> = {
    FidesInitializing: false,
    FidesInitialized: true,
    FidesConsentLoaded: true,
    FidesReady: true,
    FidesUpdating: true,
    FidesUpdated: true,
    FidesUIChanged: true,
    FidesUIShown: true,
    FidesModalClosed: true,
  };

  const eventsToDispatch = Object.entries(fidesEvents)
    .filter(([, dispatch]) => dispatch)
    .map(([key]) => key) as FidesEventType[];

  // Listen for Fides events and dispatch to Adobe
  eventsToDispatch.forEach((eventName) => {
    window.addEventListener(eventName, (event) => {
      dispatchAdobeEvent(eventName, event.detail, options);
    });
  });

  // If Fides was already initialized, dispatch a synthetic event
  if (window.Fides?.initialized) {
    const { consent, fides_meta, identity, tcf_consent } = window.Fides;
    const timestamp =
      performance?.getEntriesByName("FidesInitialized")[0]?.startTime;

    dispatchAdobeEvent(
      "FidesInitialized",
      {
        consent,
        fides_meta,
        identity,
        tcf_consent,
        timestamp,
        extraDetails: {
          consentMethod: fides_meta?.consentMethod,
        },
      },
      options
    );
  }
};
```

#### 1.2 Wire Up Integration

**File:** `clients/fides-js/src/lib/init-utils.ts`

```typescript
// Add import
import { adobe } from "../integrations/adobe";

// Add to getCoreFides return object
export const getCoreFides = ({ tcfEnabled = false }): FidesGlobal => {
  return {
    // ...existing properties
    adobe,  // <-- Add this
    gtm,
    meta,
    shopify,
    blueconic,
    // ...
  };
};
```

#### 1.3 Add TypeScript Definitions

**File:** `clients/fides-js/src/lib/consent-types.ts`

```typescript
import type { adobe } from "../integrations/adobe";

export interface FidesGlobal extends Omit<Fides, "init"> {
  // ...existing properties
  adobe: typeof adobe;  // <-- Add this
  gtm: typeof gtm;
  meta: typeof meta;
  shopify: typeof shopify;
  blueconic: typeof blueconic;
  // ...
}
```

**File:** `clients/fides-js/src/docs/fides.ts`

```typescript
/**
 * Enable the Adobe Experience Platform Launch integration. This should be
 * called immediately after FidesJS is included, and once enabled, FidesJS will
 * automatically dispatch custom events to Adobe Launch and set data elements
 * that can be used in rules and conditions.
 *
 * See the Adobe Launch tutorial for more information.
 *
 * @param options - Optional configuration for the Adobe Launch integration
 * @param options.eventPrefix - Prefix for Adobe events (default: "fides")
 * @param options.setDataElements - Whether to set data elements (default: true)
 * @param options.consentMapping - Custom consent mapping for advanced users
 *
 * @example
 * Basic usage in your site's `<head>`:
 * ```html
 * <head>
 *   <script src="path/to/fides.js"></script>
 *   <script>Fides.adobe()</script>
 * </head>
 * ```
 *
 * @example
 * With custom options:
 * ```html
 * <head>
 *   <script src="path/to/fides.js"></script>
 *   <script>
 *     Fides.adobe({
 *       eventPrefix: "privacy",
 *       setDataElements: true
 *     });
 *   </script>
 * </head>
 * ```
 */
adobe: (options?: {
  eventPrefix?: string;
  setDataElements?: boolean;
  consentMapping?: Record<string, string[]>;
}) => void;
```

#### 1.4 Update Sample App

**File:** `clients/sample-app/README.md`

```markdown
| FIDES_SAMPLE_APP__ADOBE_LAUNCH_PROPERTY_ID | (optional) Adobe Launch Property ID to inject, e.g. "AT-XXXXX" | null |
```

**File:** `clients/sample-app/src/pages/index.tsx`

```typescript
const ADOBE_PROPERTY_ID = validateEnvVar(
  process.env.NEXT_PUBLIC_FIDES_SAMPLE_APP__ADOBE_LAUNCH_PROPERTY_ID,
  /^[A-Z0-9-]+$/
);

// In component:
<Script
  id="fides-js"
  src={fidesScriptTagUrl.href}
  onReady={() => {
    // Enable Adobe integration if configured
    if (ADOBE_PROPERTY_ID) {
      (window as any).Fides.adobe();
    }
    // Enable GTM if configured
    if (GTM_CONTAINER_ID) {
      (window as any).Fides.gtm();
    }
  }}
/>

{/* Adobe Launch script */}
{ADOBE_PROPERTY_ID ? (
  <Script
    src={`https://assets.adobedtm.com/launch-${ADOBE_PROPERTY_ID}.min.js`}
    strategy="afterInteractive"
  />
) : null}
```

### Phase 2: Admin UI Support (Week 3)

#### 2.1 Update JavaScript Tag Component

**File:** `clients/admin-ui/src/features/privacy-experience/NewJavaScriptTag.tsx`

```typescript
const FIDES_ADOBE_SCRIPT_TAG = "<script>Fides.adobe()</script>";

// Update modal content:
<Text>
  3. Optionally, you can enable Adobe Experience Platform Launch for managing
  tags on your website by including the script tag below along with the
  Fides.js tag. Place it below the Fides.js script tag.
</Text>
<Code display="flex" justifyContent="space-between" alignItems="center" p={0}>
  <Text p={4}>{FIDES_ADOBE_SCRIPT_TAG}</Text>
  <ClipboardButton copyText={FIDES_ADOBE_SCRIPT_TAG} />
</Code>
```

### Phase 3: Data Discovery Support (Week 4)

#### 3.1 Add Adobe Detection Patterns

**File:** `fidesplus/tests/fixtures/website_monitor_fixtures.py`

```python
@pytest.fixture
def adobe_launch_system(db: Session) -> System:
    """Adobe Experience Platform Launch test system"""
    system = System.create(
        db=db,
        data={
            "fides_key": "adobe_experience_platform_launch",
            "system_type": "Service",
            "name": "Adobe Experience Platform Launch",
            "description": "Adobe's tag management system",
        },
    )
    yield system
    system.delete(db)
```

#### 3.2 Update Detection Patterns

Add Adobe Launch URLs to detection patterns:
- `assets.adobedtm.com`
- `*.adoberesources.net`
- `*.adobedtm.com`

### Phase 4: Testing (Week 5)

#### 4.1 Unit Tests

**File:** `clients/fides-js/__tests__/integrations/adobe.test.ts`

```typescript
import { adobe } from "../../src/integrations/adobe";

describe("Adobe Launch Integration", () => {
  beforeEach(() => {
    // Mock _satellite
    window._satellite = {
      track: jest.fn(),
      setVar: jest.fn(),
      getVar: jest.fn(),
      logger: { log: jest.fn() },
    };
  });

  it("should dispatch events to Adobe Launch", () => {
    adobe();

    window.dispatchEvent(new CustomEvent("FidesReady", {
      detail: {
        consent: { analytics: true, marketing: false },
        timestamp: Date.now(),
      }
    }));

    expect(window._satellite.track).toHaveBeenCalledWith(
      "fides:FidesReady",
      expect.objectContaining({
        consent: { analytics: true, marketing: false }
      })
    );
  });

  it("should set data elements when enabled", () => {
    adobe({ setDataElements: true });

    window.dispatchEvent(new CustomEvent("FidesReady", {
      detail: {
        consent: { analytics: true },
        timestamp: 12345,
      }
    }));

    expect(window._satellite.setVar).toHaveBeenCalledWith(
      "fides-consent",
      expect.objectContaining({ analytics: true })
    );
  });

  it("should use custom event prefix", () => {
    adobe({ eventPrefix: "privacy" });

    window.dispatchEvent(new CustomEvent("FidesReady", {
      detail: { consent: {}, timestamp: 0 }
    }));

    expect(window._satellite.track).toHaveBeenCalledWith(
      "privacy:FidesReady",
      expect.any(Object)
    );
  });
});
```

#### 4.2 Cypress E2E Tests

**File:** `clients/privacy-center/cypress/e2e/fides-js/consent-adobe.cy.ts`

```typescript
describe("Adobe Launch Integration", () => {
  beforeEach(() => {
    cy.window().then((win) => {
      // Mock Adobe _satellite
      win._satellite = {
        track: cy.stub().as("adobeTrack"),
        setVar: cy.stub().as("adobeSetVar"),
        getVar: cy.stub().as("adobeGetVar"),
        logger: { log: cy.stub() },
      };
    });

    cy.visit("/");
  });

  it("dispatches Fides events to Adobe Launch", () => {
    cy.waitUntilFidesInitialized();

    cy.get("@adobeTrack").should("have.been.calledWith",
      "fides:FidesReady",
      Cypress.sinon.match.object
    );
  });

  it("sets Adobe data elements with consent values", () => {
    cy.waitUntilFidesInitialized();

    cy.get("@adobeSetVar").should("have.been.calledWith",
      "fides-consent",
      Cypress.sinon.match.object
    );
  });
});
```

#### 4.3 Manual Testing Checklist

- [ ] Adobe Launch Property created in Adobe Experience Cloud
- [ ] Fides.adobe() script tag added to test page
- [ ] Adobe Launch library loads successfully
- [ ] Fides events appear in Adobe debugger
- [ ] Data elements populate with consent values
- [ ] Rules trigger based on consent state
- [ ] Tags fire/block according to consent
- [ ] Consent updates propagate to Adobe in real-time
- [ ] Works with TCF experiences
- [ ] Works with non-TCF experiences
- [ ] Works with GPP experiences

### Phase 5: Documentation (Week 6)

#### 5.1 Tutorial Documentation

**File:** `docs/fides/docs/tutorials/consent-management/adobe-launch-integration.md`

```markdown
# Adobe Experience Platform Launch Integration

This tutorial shows you how to integrate Fides consent management with
Adobe Experience Platform Launch (Adobe Launch).

## Prerequisites

- Fides.js installed on your website
- Adobe Launch property configured
- Access to Adobe Experience Platform Launch

## Step 1: Add Fides.adobe() Script

Add the Fides.adobe() integration immediately after your Fides.js script:

```html
<head>
  <!-- Fides.js script -->
  <script src="https://your-privacy-center.com/fides.js"></script>

  <!-- Enable Adobe integration -->
  <script>Fides.adobe()</script>

  <!-- Adobe Launch library -->
  <script src="https://assets.adobedtm.com/launch-XXXXX.min.js"></script>
</head>
```

## Step 2: Configure Data Elements in Adobe Launch

Create data elements to access Fides consent:

1. In Adobe Launch, navigate to Data Elements
2. Create a new Custom Code data element named "Fides Consent Analytics"
3. Use this code:

```javascript
return window.Fides && window.Fides.consent && window.Fides.consent.analytics;
```

Repeat for other consent categories (marketing, functional, etc.)

## Step 3: Create Rules for Consent-Based Firing

Create rules that check consent before firing tags:

1. Navigate to Rules in Adobe Launch
2. Create a new rule "Fire Analytics Only If Consented"
3. Add Event: Custom Event, event name: `fides:FidesReady`
4. Add Condition: Custom Code:

```javascript
return window.Fides.consent.analytics === true;
```

5. Add Action: Adobe Analytics - Send Beacon

## Step 4: Block Tags Based on Consent

For tags that should be blocked without consent:

1. Add a condition to each rule checking consent
2. Use data elements in conditions
3. Test with Adobe Debugger

## Configuration Options

```javascript
Fides.adobe({
  eventPrefix: 'privacy',        // Custom event prefix
  setDataElements: true,         // Enable data elements
  consentMapping: {              // Custom consent mapping
    analytics: ['analytics'],
    marketing: ['marketing', 'data_sales_and_sharing']
  }
});
```

## Available Fides Events in Adobe

These custom events are dispatched to Adobe Launch:

- `fides:FidesInitialized` - Initial consent loaded
- `fides:FidesReady` - Fides fully ready
- `fides:FidesConsentLoaded` - Consent loaded from cookie
- `fides:FidesUpdating` - User is updating consent
- `fides:FidesUpdated` - Consent updated
- `fides:FidesUIShown` - Consent UI shown
- `fides:FidesUIChanged` - UI state changed
- `fides:FidesModalClosed` - Modal closed

## Data Elements Available

- `fides-consent` - Full consent object
- `fides-timestamp` - Timestamp of last consent update

## Troubleshooting

### Events Not Firing

Check Adobe Debugger (_satellite.setDebug(true)) to see events.

### Consent Not Updating

Ensure Fides.adobe() is called after Fides.js loads.

### Tags Firing Despite No Consent

Check rule conditions and ensure they reference Fides data elements.
```

#### 5.2 API Documentation

**File:** `clients/fides-js/docs/interfaces/Fides.md`

Update with Adobe integration details similar to GTM section.

#### 5.3 Migration Guide

**File:** `docs/fides/docs/guides/adobe-launch-migration.md`

Guide for users migrating from other CMPs to Fides with Adobe Launch.

### Phase 6: Shared Utilities Extraction (Week 7)

Create reusable utilities to reduce duplication:

#### 6.1 Consent Mapper Utility

**File:** `clients/fides-js/src/integrations/utils/consent-mapper.ts`

```typescript
import { NoticeConsent } from "../../lib/consent-types";

export type ConsentMapping = Record<string, string[]>;

export interface MappedConsent {
  [key: string]: boolean | undefined;
}

/**
 * Map Fides consent to target system consent using a mapping configuration.
 *
 * @param fidesConsent - Fides consent object
 * @param mapping - Mapping of target keys to Fides notice keys
 * @returns Mapped consent object
 *
 * @example
 * ```typescript
 * const mapped = mapConsentByKeys(
 *   { analytics: true, marketing: false },
 *   { analytics_enabled: ['analytics'], ads_enabled: ['marketing'] }
 * );
 * // Returns: { analytics_enabled: true, ads_enabled: false }
 * ```
 */
export function mapConsentByKeys(
  fidesConsent: NoticeConsent,
  mapping: ConsentMapping
): MappedConsent {
  const result: MappedConsent = {};

  for (const [targetKey, sourceKeys] of Object.entries(mapping)) {
    const hasTrue = sourceKeys.some(key => fidesConsent[key] === true);
    const hasFalse = sourceKeys.some(key => fidesConsent[key] === false);

    if (hasTrue) {
      result[targetKey] = true;
    } else if (hasFalse) {
      result[targetKey] = false;
    }
    // If neither, leave undefined (allows default handling)
  }

  return result;
}
```

#### 6.2 Update Existing Integrations

Refactor GTM, Adobe, and Shopify to use shared utilities:

```typescript
// In gtm.ts
import { mapConsentByKeys } from "./utils/consent-mapper";

// Replace inline mapping logic with:
const mappedConsent = mapConsentByKeys(detail.consent, CONSENT_MAP);
```

---

## Testing Strategy

### Unit Test Coverage

- ✅ Adobe integration initializes correctly
- ✅ Events dispatch to _satellite.track()
- ✅ Data elements set via _satellite.setVar()
- ✅ Custom event prefix works
- ✅ Custom consent mapping works
- ✅ setDataElements option respected
- ✅ Handles missing _satellite gracefully
- ✅ Handles late initialization (Fides ready before adobe())

### Integration Test Coverage

- ✅ Full Fides + Adobe Launch flow in Cypress
- ✅ Real Adobe Launch library integration
- ✅ Event dispatch and rule triggering
- ✅ Data element population
- ✅ Consent updates propagate
- ✅ Multiple consent changes handled
- ✅ TCF experience compatibility
- ✅ GPP experience compatibility

### Manual Testing Checklist

#### Setup
- [ ] Adobe Launch property created
- [ ] Development environment configured
- [ ] Staging environment configured
- [ ] Adobe Debugger browser extension installed

#### Functional Tests
- [ ] Fides.adobe() initializes
- [ ] Adobe Launch library loads
- [ ] Custom events dispatch correctly
- [ ] Data elements populate
- [ ] Rules trigger based on consent
- [ ] Tags fire when consent granted
- [ ] Tags blocked when consent denied
- [ ] Consent updates trigger rule re-evaluation

#### Edge Cases
- [ ] Adobe Launch loads after Fides
- [ ] Fides loads after Adobe Launch
- [ ] Multiple rapid consent changes
- [ ] Browser back/forward navigation
- [ ] Page refresh preserves consent
- [ ] Cross-domain consent (if applicable)

#### Browser Compatibility
- [ ] Chrome
- [ ] Firefox
- [ ] Safari
- [ ] Edge
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)

#### Performance
- [ ] No JavaScript errors in console
- [ ] No memory leaks
- [ ] Event dispatch latency < 50ms
- [ ] No excessive event firing

---

## Documentation Requirements

### User-Facing Documentation

1. **Tutorial: Adobe Launch Integration**
   - Step-by-step setup guide
   - Screenshots of Adobe Launch UI
   - Example rules and data elements
   - Troubleshooting section

2. **API Reference**
   - `Fides.adobe()` options
   - Event names and payloads
   - Data element structure
   - Code examples

3. **Migration Guide**
   - Migrating from other CMPs
   - Migrating from OneTrust + Adobe
   - Migrating from Cookie Pro + Adobe
   - Common pitfalls

4. **Best Practices**
   - Rule organization
   - Data element naming conventions
   - Performance optimization
   - Testing strategies

### Developer Documentation

1. **Architecture Overview**
   - Integration design
   - Event flow diagrams
   - Sequence diagrams
   - Data structures

2. **Code Comments**
   - JSDoc for all public functions
   - Inline comments for complex logic
   - Type definitions with descriptions

3. **Testing Guide**
   - How to run tests
   - How to add new tests
   - Testing utilities
   - Mocking strategies

### Internal Documentation

1. **Implementation Notes**
   - Design decisions
   - Alternatives considered
   - Known limitations
   - Future improvements

2. **Maintenance Guide**
   - How to update
   - How to debug
   - How to add features
   - How to handle breaking changes

---

## Timeline & Resources

### Timeline

| Phase | Duration | Deliverables |
|-------|----------|-------------|
| **Phase 1:** Core Integration | 2 weeks | Working `Fides.adobe()` integration |
| **Phase 2:** Admin UI | 1 week | UI support for installation |
| **Phase 3:** Data Discovery | 1 week | Adobe asset detection |
| **Phase 4:** Testing | 1 week | Comprehensive test suite |
| **Phase 5:** Documentation | 1 week | Complete user & dev docs |
| **Phase 6:** Shared Utilities | 1 week | Refactor with shared code |
| **Buffer** | 1 week | Bug fixes, polish, review |
| **Total** | **8 weeks** | Production-ready integration |

### Resources Required

#### Engineering

- **1 Senior Frontend Engineer** (8 weeks)
  - Core integration implementation
  - Testing
  - Code reviews

- **1 Frontend Engineer** (4 weeks)
  - Admin UI updates
  - Sample app updates
  - E2E tests

- **1 Backend Engineer** (2 weeks)
  - Data discovery updates
  - Asset detection patterns

#### QA

- **1 QA Engineer** (2 weeks)
  - Manual testing
  - Test plan creation
  - Bug verification

#### Documentation

- **1 Technical Writer** (2 weeks)
  - Tutorial documentation
  - API documentation
  - Migration guides

#### Design (Optional)

- **1 Designer** (1 week)
  - UI updates if needed
  - Documentation screenshots
  - Diagrams

### Dependencies

- ✅ Fides.js v2.0+ (current version)
- ✅ Adobe Launch account for testing
- ✅ Adobe Debugger extension
- ⚠️ Adobe Launch sandbox environment (need to request)

### Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Adobe Launch API changes | High | Low | Use stable API surface, add versioning |
| Cross-domain complexity | Medium | Medium | Test thoroughly, document limitations |
| Browser compatibility issues | Medium | Low | Test all browsers, use polyfills |
| Performance impact | Medium | Low | Benchmark, optimize event dispatch |
| Documentation gaps | Medium | Medium | Allocate dedicated writer, peer review |
| Customer confusion | High | Medium | Create migration guides, offer support |

---

## Success Metrics

### Technical Metrics

- ✅ 100% test coverage for Adobe integration
- ✅ < 1ms event dispatch latency
- ✅ Zero console errors
- ✅ Zero memory leaks
- ✅ Works in all major browsers

### Business Metrics

- ✅ 5+ customers successfully integrate in first month
- ✅ < 5 support tickets per month
- ✅ Positive customer feedback (NPS > 8)
- ✅ Documentation page views > 500/month
- ✅ Tutorial completion rate > 60%

### Adoption Metrics

- ✅ 20% of new customers choose Adobe over GTM
- ✅ 10% of existing GTM customers migrate to Adobe
- ✅ Adobe integration mentioned in 3+ case studies

---

## Future Enhancements

### Short-term (Next 3-6 months)

1. **Adobe Analytics Direct Integration**
   - Bypass Launch for direct Analytics integration
   - Faster performance
   - Simpler setup for Analytics-only customers

2. **Adobe Audience Manager Integration**
   - Segment users based on consent
   - Privacy-compliant audience building

3. **Visual UI for Consent Mapping**
   - Admin UI for custom consent mappings
   - No-code configuration

### Medium-term (6-12 months)

1. **Tag Manager Integration Framework**
   - Abstract common patterns
   - Make adding new tag managers easier
   - Reduce maintenance burden

2. **Additional Tag Managers**
   - Tealium (requested by customers)
   - Segment (requested by customers)
   - Matomo Tag Manager

3. **Advanced Adobe Features**
   - Server-side Launch integration
   - Mobile SDK integration
   - AEP Web SDK integration

### Long-term (12+ months)

1. **Unified Consent Hub**
   - Manage all tag manager integrations
   - Cross-platform consent sync
   - Enterprise consent governance

2. **AI-Powered Consent Optimization**
   - Automatic tag categorization
   - Consent prompt optimization
   - Compliance recommendations

---

## Appendix

### A. Adobe Launch Terminology

- **Property:** A container for all Launch configuration
- **Environment:** Dev, staging, or production version of property
- **Rule:** Combination of events, conditions, and actions
- **Data Element:** Variable accessible throughout Launch
- **Extension:** Plugin that adds functionality
- **Library:** Published bundle of rules and extensions

### B. Comparison: GTM vs Adobe Launch

| Feature | GTM | Adobe Launch |
|---------|-----|--------------|
| **Data Layer** | Single array (`dataLayer`) | Custom object + _satellite |
| **Event Model** | Push to array | Direct dispatch |
| **Consent API** | Native Consent Mode | Custom implementation |
| **Extensions** | Community templates | Full extensions |
| **Pricing** | Free (Google 360 for premium) | Part of Adobe Experience Cloud |
| **Learning Curve** | Moderate | Steeper |
| **Enterprise Features** | Basic | Advanced |
| **Third-party Tags** | Excellent support | Excellent support |

### C. Code Examples

#### Example Adobe Launch Rule

**Rule Name:** Fire Google Analytics on Consent

**Event:** Custom Event
```javascript
Event Name: fides:FidesReady
```

**Condition:** Custom Code
```javascript
return window.Fides && window.Fides.consent && window.Fides.consent.analytics === true;
```

**Action:** Google Analytics - Send Pageview

#### Example Data Element

**Name:** Fides Marketing Consent

**Type:** Custom Code

**Code:**
```javascript
return window.Fides && window.Fides.consent ? window.Fides.consent.marketing : null;
```

### D. Resources

- [Adobe Launch Documentation](https://experienceleague.adobe.com/docs/experience-platform/tags/home.html)
- [Adobe Experience Cloud](https://business.adobe.com/products/experience-cloud.html)
- [Fides Documentation](https://docs.ethyca.com/)
- [Google Tag Manager Migration Guide](https://experienceleague.adobe.com/docs/platform-learn/data-collection/tags/migration-from-google-tag-manager.html)

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-05 | AI Assistant | Initial draft based on GTM analysis |

---

## Approval & Sign-off

- [ ] Engineering Lead Review
- [ ] Product Manager Review
- [ ] Architecture Review Board
- [ ] Security Review
- [ ] Legal/Compliance Review

---

**Next Steps:**

1. Review this document with engineering team
2. Get customer input on Adobe Launch needs
3. Set up Adobe Launch test environment
4. Begin Phase 1 implementation
5. Schedule weekly progress reviews
