# Adobe Experience Platform Integration - Proof of Concept

**Document Version:** 1.0
**Date:** November 6, 2025
**Status:** POC Scope
**Goal:** Minimum viable demo to prove Fides → Adobe integration works

---

## Executive Summary

This document defines the **absolute minimum** implementation needed to demonstrate that Fides can control Adobe Experience Platform consent. This is a **proof of concept** to validate the approach before building the full feature.

### What's Included (POC Scope)
- ✅ `Fides.adobe()` method with hardcoded mappings
- ✅ Adobe Web SDK (Consent v2) integration only
- ✅ Basic custom event dispatching
- ✅ Single Adobe Launch rule template
- ✅ Smoke tests only

### What's Excluded (Post-POC)
- ❌ ECID Opt-In Service (legacy - defer to full implementation)
- ❌ OneTrust migration (not needed for POC)
- ❌ Admin UI (use hardcoded config)
- ❌ Configurable mappings (hardcode defaults)
- ❌ Comprehensive testing (just smoke tests)
- ❌ Full documentation (just basic example)

### Success Criteria
Can we show a customer:
1. Fides consent modal appears
2. User opts in/out
3. Adobe Web SDK receives consent update
4. Adobe Analytics tag fires (or doesn't) based on consent
5. Visible in Adobe Experience Platform Debugger

---

## POC Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Demo Page                               │
│                                                              │
│  <script src="fides.js"></script>                          │
│  <script>Fides.adobe()</script>  ← NEW POC CODE            │
│  <script src="adobe-launch.js"></script>                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│               Fides.adobe() (POC)                            │
│                                                              │
│  • Hardcoded mapping: analytics → collect+measure           │
│  • Listen for FidesReady, FidesUpdated                      │
│  • Call alloy("setConsent", {...})                          │
│  • Dispatch fides:ready event                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Adobe Web SDK                                   │
│                                                              │
│  • Receives setConsent() call                               │
│  • Updates consent state                                    │
│  • Fires/blocks Adobe Analytics                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Stories

### Story 1: Core Adobe Web SDK Integration (POC)
**Points: 8**

**As a developer, I want a minimal `Fides.adobe()` integration that triggers Adobe Web SDK consent**

**Acceptance Criteria:**
- [ ] `Fides.adobe()` function exists and is callable
- [ ] Listens for `FidesReady` and `FidesUpdated` events
- [ ] Calls `alloy("setConsent", {...})` with Adobe Consent v2 format
- [ ] Hardcoded mapping: `analytics` → `collect: true, measure: true`
- [ ] Hardcoded mapping: `advertising` → `share: true`
- [ ] Hardcoded mapping: `functional` → `personalize: true`
- [ ] Works in Chrome with Adobe Experience Platform Debugger

**Implementation:**

**File:** `clients/fides-js/src/integrations/adobe.ts`

```typescript
/**
 * POC: Minimal Adobe Experience Platform Integration
 *
 * This is a proof-of-concept implementation with hardcoded mappings.
 * Full implementation will support:
 * - Configurable mappings (from Admin UI)
 * - ECID Opt-In Service (legacy)
 * - OneTrust migration
 * - Regional defaults
 */

import { NoticeConsent } from "../lib/consent-types";
import { FidesEventDetail } from "../lib/events";

declare global {
  interface Window {
    alloy?: (command: string, options: any) => Promise<any>;
  }
}

/**
 * Hardcoded consent mapping for POC
 * TODO: Make configurable via Admin UI
 */
const HARDCODED_MAPPING = {
  // Adobe purpose → Fides notice keys
  collect: ["analytics"],
  measure: ["analytics"],
  personalize: ["functional"],
  share: ["advertising", "data_sales_and_sharing"]
};

/**
 * Map Fides consent to Adobe Web SDK Consent v2 format
 */
function mapFidesToAdobeConsent(fidesConsent: NoticeConsent): any {
  const adobeConsent: any = {};

  // Map each Adobe purpose
  for (const [adobePurpose, fidesNotices] of Object.entries(HARDCODED_MAPPING)) {
    // Check if ANY of the Fides notices are opted-in
    const hasConsent = fidesNotices.some(notice => {
      const value = fidesConsent[notice];
      return value === true || value === "opt_in" || value === "acknowledge";
    });

    adobeConsent[adobePurpose] = { val: hasConsent ? "y" : "n" };
  }

  return adobeConsent;
}

/**
 * Call Adobe Web SDK setConsent
 */
function callAdobeSetConsent(fidesConsent: NoticeConsent) {
  if (typeof window.alloy !== "function") {
    console.warn("[Fides Adobe POC] Adobe Web SDK (alloy) not found");
    return;
  }

  const adobeConsent = mapFidesToAdobeConsent(fidesConsent);

  const payload = {
    consent: [{
      standard: "Adobe",
      version: "2.0",
      value: adobeConsent
    }]
  };

  console.log("[Fides Adobe POC] Calling setConsent:", payload);

  window.alloy("setConsent", payload)
    .then(() => {
      console.log("[Fides Adobe POC] Adobe consent updated successfully");
    })
    .catch((error: Error) => {
      console.error("[Fides Adobe POC] Error updating Adobe consent:", error);
    });
}

/**
 * Handle Fides consent events
 */
function handleFidesConsent(event: CustomEvent<FidesEventDetail>) {
  const { consent } = event.detail;

  console.log("[Fides Adobe POC] Fides consent event:", event.type, consent);

  callAdobeSetConsent(consent);

  // Also dispatch custom event for Adobe Launch rules
  window.dispatchEvent(new CustomEvent("fides:ready", {
    detail: { consent }
  }));
}

/**
 * Initialize Adobe integration (POC version)
 *
 * @example
 * <script>Fides.adobe()</script>
 */
export const adobe = () => {
  console.log("[Fides Adobe POC] Initializing Adobe integration");

  // Listen for Fides events
  window.addEventListener("FidesReady", handleFidesConsent as EventListener);
  window.addEventListener("FidesUpdated", handleFidesConsent as EventListener);

  // If Fides already initialized, trigger immediately
  if (window.Fides?.initialized && window.Fides?.consent) {
    console.log("[Fides Adobe POC] Fides already initialized, triggering consent");
    callAdobeSetConsent(window.Fides.consent);
  }

  console.log("[Fides Adobe POC] Initialization complete");
};
```

**File:** `clients/fides-js/src/lib/init-utils.ts` (add import)

```typescript
import { adobe } from "../integrations/adobe";

export const getCoreFides = ({ tcfEnabled = false }): FidesGlobal => {
  return {
    // ...existing
    adobe,  // Add this
    gtm,
    shopify,
    // ...
  };
};
```

**File:** `clients/fides-js/src/lib/consent-types.ts` (add type)

```typescript
import type { adobe } from "../integrations/adobe";

export interface FidesGlobal extends Omit<Fides, "init"> {
  adobe: typeof adobe;  // Add this
  // ...existing
}
```

**Test Plan:**
- Manual test with Adobe Experience Platform Debugger
- Verify console logs show consent updates
- Verify Adobe Debugger shows consent state changes

---

### Story 2: Adobe Launch Rule Template
**Points: 3**

**As a customer, I want a copy-paste Adobe Launch rule that responds to Fides consent**

**Acceptance Criteria:**
- [ ] Documented rule configuration for Adobe Launch
- [ ] Uses custom event trigger (`fides:ready`)
- [ ] Calls Adobe Analytics only when consent granted
- [ ] Tested in Adobe Launch property

**Deliverable:**

**Adobe Launch Rule Configuration**

**Rule Name:** "Set Adobe Consent from Fides (POC)"

**Event Configuration:**
- Event Type: Custom Event
- Event Name: `fides:ready`

**Condition:** (None - always fire)

**Action Configuration:**
- Extension: Adobe Experience Platform Web SDK
- Action Type: Custom Code
- Code:
```javascript
// POC: Simple Adobe consent update
var consent = window.Fides && window.Fides.consent;

if (!consent) {
  console.warn("Fides consent not available");
  return;
}

// Map Fides to Adobe
var adobeConsent = {
  collect: { val: consent.analytics ? "y" : "n" },
  measure: { val: consent.analytics ? "y" : "n" },
  personalize: { val: consent.functional ? "y" : "n" },
  share: { val: consent.advertising ? "y" : "n" }
};

// Call setConsent
alloy("setConsent", {
  consent: [{
    standard: "Adobe",
    version: "2.0",
    value: adobeConsent
  }]
});
```

**Alternative Rule (for tag gating):**

**Rule Name:** "Fire Analytics Only If Consented (POC)"

**Event:** Page Load - DOM Ready

**Condition:** Custom Code
```javascript
return window.Fides && window.Fides.consent && window.Fides.consent.analytics === true;
```

**Action:** Adobe Analytics - Send Beacon

---

### Story 3: POC Demo Page
**Points: 3**

**As a stakeholder, I want a working demo page to see the integration in action**

**Acceptance Criteria:**
- [ ] Single HTML page with Fides + Adobe
- [ ] Shows consent modal
- [ ] Adobe Experience Platform Debugger shows consent updates
- [ ] Can opt-in/out and see Adobe Analytics fire/block
- [ ] README with setup instructions

**Deliverable:**

**File:** `clients/fides-js/examples/adobe-poc.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Fides + Adobe POC</title>

  <!-- 1. Adobe Web SDK (alloy) - Load FIRST -->
  <script>
    !function(n,o){o.forEach(function(o){n[o]||((n.__alloyNS=n.__alloyNS||[]).push(o),
    n[o]=function(){var u=arguments;return new Promise(function(i,l){n[o].q.push([i,l,u])})},
    n[o].q=[])})}(window,["alloy"]);

    // Configure Adobe Web SDK
    alloy("configure", {
      // TODO: Replace with actual Adobe datastream ID
      datastreamId: "YOUR_DATASTREAM_ID",
      orgId: "YOUR_ORG_ID@AdobeOrg",
      defaultConsent: "pending"  // Important: Wait for Fides
    });
  </script>
  <script src="https://cdn1.adoberesources.net/alloy/2.19.0/alloy.min.js" async></script>

  <!-- 2. Fides JS -->
  <script src="https://privacy-demo.ethyca.com/fides.js"></script>

  <!-- 3. Enable Adobe Integration -->
  <script>
    console.log("Enabling Fides Adobe integration (POC)");
    Fides.adobe();
  </script>

  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      max-width: 800px;
      margin: 40px auto;
      padding: 20px;
      line-height: 1.6;
    }

    .status-box {
      background: #f5f5f5;
      border: 1px solid #ddd;
      border-radius: 4px;
      padding: 20px;
      margin: 20px 0;
    }

    .consent-status {
      display: flex;
      gap: 20px;
      margin: 20px 0;
    }

    .consent-item {
      flex: 1;
      background: white;
      border: 1px solid #ddd;
      border-radius: 4px;
      padding: 15px;
    }

    .consent-item.granted {
      border-color: #4CAF50;
      background: #f1f8f4;
    }

    .consent-item.denied {
      border-color: #f44336;
      background: #fef5f5;
    }

    button {
      background: #007bff;
      color: white;
      border: none;
      padding: 10px 20px;
      border-radius: 4px;
      cursor: pointer;
      font-size: 14px;
      margin-right: 10px;
    }

    button:hover {
      background: #0056b3;
    }

    .log {
      background: #1e1e1e;
      color: #00ff00;
      font-family: monospace;
      font-size: 12px;
      padding: 15px;
      border-radius: 4px;
      max-height: 300px;
      overflow-y: auto;
      margin: 20px 0;
    }

    .log-entry {
      margin: 5px 0;
    }
  </style>
</head>
<body>
  <h1>🧪 Fides + Adobe Experience Platform - POC</h1>

  <div class="status-box">
    <h2>Integration Status</h2>
    <p id="integration-status">⏳ Waiting for Fides to initialize...</p>
  </div>

  <div class="status-box">
    <h2>Current Consent State</h2>
    <div class="consent-status" id="consent-status">
      <div class="consent-item">
        <strong>Analytics</strong>
        <p id="analytics-status">Unknown</p>
      </div>
      <div class="consent-item">
        <strong>Advertising</strong>
        <p id="advertising-status">Unknown</p>
      </div>
      <div class="consent-item">
        <strong>Functional</strong>
        <p id="functional-status">Unknown</p>
      </div>
    </div>
  </div>

  <div class="status-box">
    <h2>Test Actions</h2>
    <button onclick="window.Fides.showModal()">
      Show Fides Modal
    </button>
    <button onclick="testAdobeAnalytics()">
      Fire Adobe Analytics Event
    </button>
    <button onclick="clearLogs()">
      Clear Logs
    </button>
  </div>

  <div class="status-box">
    <h2>Event Log</h2>
    <div class="log" id="event-log"></div>
  </div>

  <div class="status-box">
    <h2>Setup Instructions</h2>
    <ol>
      <li>Install <a href="https://chrome.google.com/webstore/detail/adobe-experience-platform/bfnnokhpnncpkdmbokanobigaccjkpob" target="_blank">Adobe Experience Platform Debugger</a></li>
      <li>Update <code>datastreamId</code> and <code>orgId</code> in the script above</li>
      <li>Open Adobe Debugger and navigate to this page</li>
      <li>Interact with Fides consent modal</li>
      <li>Watch Adobe Debugger show consent state changes</li>
    </ol>

    <h3>What to Verify:</h3>
    <ul>
      <li>✅ Fides modal appears on page load</li>
      <li>✅ Adobe Web SDK shows "pending" consent initially</li>
      <li>✅ After opt-in, Adobe Debugger shows consent "granted"</li>
      <li>✅ After opt-out, Adobe Debugger shows consent "denied"</li>
      <li>✅ Adobe Analytics beacon fires only when consented</li>
    </ul>
  </div>

  <script>
    // Event logging
    const eventLog = document.getElementById('event-log');
    const integrationStatus = document.getElementById('integration-status');

    function log(message, type = 'info') {
      const entry = document.createElement('div');
      entry.className = 'log-entry';
      const timestamp = new Date().toLocaleTimeString();
      entry.textContent = `[${timestamp}] ${message}`;
      eventLog.appendChild(entry);
      eventLog.scrollTop = eventLog.scrollHeight;
      console.log(message);
    }

    function clearLogs() {
      eventLog.innerHTML = '';
    }

    function updateConsentStatus() {
      if (!window.Fides || !window.Fides.consent) return;

      const consent = window.Fides.consent;

      // Update analytics
      const analyticsEl = document.getElementById('analytics-status').parentElement;
      const analyticsStatus = consent.analytics === true ? '✅ Granted' : '❌ Denied';
      document.getElementById('analytics-status').textContent = analyticsStatus;
      analyticsEl.className = consent.analytics === true ? 'consent-item granted' : 'consent-item denied';

      // Update advertising
      const advertisingEl = document.getElementById('advertising-status').parentElement;
      const advertisingStatus = consent.advertising === true ? '✅ Granted' : '❌ Denied';
      document.getElementById('advertising-status').textContent = advertisingStatus;
      advertisingEl.className = consent.advertising === true ? 'consent-item granted' : 'consent-item denied';

      // Update functional
      const functionalEl = document.getElementById('functional-status').parentElement;
      const functionalStatus = consent.functional === true ? '✅ Granted' : '❌ Denied';
      document.getElementById('functional-status').textContent = functionalStatus;
      functionalEl.className = consent.functional === true ? 'consent-item granted' : 'consent-item denied';
    }

    function testAdobeAnalytics() {
      log('🧪 Attempting to fire Adobe Analytics event...');

      if (window.Fides.consent.analytics !== true) {
        log('⚠️  Analytics consent not granted - event should be blocked');
      } else {
        log('✅ Analytics consent granted - event should fire');
      }

      alloy("sendEvent", {
        xdm: {
          eventType: "web.webpagedetails.pageViews",
          web: {
            webPageDetails: {
              name: "POC Test Page"
            }
          }
        }
      }).then(function(result) {
        log('✅ Adobe Analytics event sent successfully');
      }).catch(function(error) {
        log('❌ Adobe Analytics event failed: ' + error.message);
      });
    }

    // Listen for Fides events
    window.addEventListener('FidesReady', function(event) {
      log('🎉 FidesReady event fired');
      log('   Consent: ' + JSON.stringify(event.detail.consent));
      integrationStatus.textContent = '✅ Fides initialized and Adobe integration active';
      integrationStatus.style.color = '#4CAF50';
      updateConsentStatus();
    });

    window.addEventListener('FidesUpdated', function(event) {
      log('🔄 FidesUpdated event fired');
      log('   Consent: ' + JSON.stringify(event.detail.consent));
      updateConsentStatus();
    });

    window.addEventListener('fides:ready', function(event) {
      log('📡 Custom fides:ready event dispatched for Adobe Launch');
    });

    // Log Adobe alloy calls
    const originalAlloy = window.alloy;
    window.alloy = function(command, options) {
      if (command === 'setConsent') {
        log('📤 Adobe setConsent called: ' + JSON.stringify(options));
      }
      return originalAlloy.apply(this, arguments);
    };

    log('🚀 POC page loaded - waiting for Fides initialization...');
  </script>
</body>
</html>
```

**File:** `clients/fides-js/examples/README-adobe-poc.md`

```markdown
# Adobe Experience Platform Integration - POC

This is a minimal proof-of-concept demonstrating Fides controlling Adobe consent.

## Setup

1. **Get Adobe Credentials:**
   - Log into Adobe Experience Platform
   - Create or use existing Datastream
   - Note your `datastreamId` and `orgId`

2. **Update Demo Page:**
   - Edit `adobe-poc.html`
   - Replace `YOUR_DATASTREAM_ID` and `YOUR_ORG_ID` with real values

3. **Install Browser Extension:**
   - Install [Adobe Experience Platform Debugger](https://chrome.google.com/webstore/detail/adobe-experience-platform/bfnnokhpnncpkdmbokanobigaccjkpob)

4. **Run Demo:**
   ```bash
   # Serve the file locally
   python3 -m http.server 8000
   # Or just open the file in browser
   open adobe-poc.html
   ```

5. **Open Adobe Debugger:**
   - Click extension icon
   - Navigate to "Consent" tab
   - Watch consent state update as you interact with Fides

## Expected Behavior

1. Page loads with Fides modal
2. Adobe Web SDK consent state: "pending"
3. User opts in via Fides modal
4. Adobe consent updates to "granted" for opted-in purposes
5. Adobe Analytics beacon fires
6. User opts out
7. Adobe consent updates to "denied"
8. Adobe Analytics beacon blocked

## Troubleshooting

**Adobe Web SDK not found:**
- Check browser console for errors
- Verify alloy.min.js loaded

**Consent not updating:**
- Check `Fides.adobe()` was called
- Verify FidesReady event fired (check console)
- Look for Adobe setConsent calls in console

**Adobe Debugger shows no data:**
- Verify datastreamId and orgId are correct
- Check network tab for Adobe requests
- Ensure Adobe Debugger is enabled
```

---

### Story 4: Basic Smoke Tests
**Points: 2**

**As a developer, I want basic tests to ensure POC doesn't break**

**Acceptance Criteria:**
- [ ] Test that `Fides.adobe()` is callable
- [ ] Test that Adobe setConsent is called on FidesReady
- [ ] Test that consent mapping works correctly
- [ ] Tests pass in CI

**Implementation:**

**File:** `clients/fides-js/__tests__/integrations/adobe-poc.test.ts`

```typescript
import { adobe } from "../../src/integrations/adobe";

describe("Adobe Integration POC", () => {
  let mockAlloy: jest.Mock;

  beforeEach(() => {
    // Mock alloy function
    mockAlloy = jest.fn().mockResolvedValue({});
    (window as any).alloy = mockAlloy;

    // Mock Fides
    (window as any).Fides = {
      initialized: false,
      consent: {}
    };
  });

  afterEach(() => {
    delete (window as any).alloy;
    delete (window as any).Fides;
  });

  it("should be callable", () => {
    expect(() => adobe()).not.toThrow();
  });

  it("should call alloy setConsent on FidesReady", async () => {
    adobe();

    // Simulate FidesReady event
    const event = new CustomEvent("FidesReady", {
      detail: {
        consent: {
          analytics: true,
          advertising: false,
          functional: true
        }
      }
    });

    window.dispatchEvent(event);

    // Wait for async
    await new Promise(resolve => setTimeout(resolve, 0));

    expect(mockAlloy).toHaveBeenCalledWith("setConsent", {
      consent: [{
        standard: "Adobe",
        version: "2.0",
        value: {
          collect: { val: "y" },  // analytics = true
          measure: { val: "y" },  // analytics = true
          personalize: { val: "y" },  // functional = true
          share: { val: "n" }  // advertising = false
        }
      }]
    });
  });

  it("should handle missing alloy gracefully", () => {
    delete (window as any).alloy;

    const consoleSpy = jest.spyOn(console, "warn").mockImplementation();

    adobe();

    const event = new CustomEvent("FidesReady", {
      detail: { consent: { analytics: true } }
    });

    expect(() => window.dispatchEvent(event)).not.toThrow();
    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining("Adobe Web SDK (alloy) not found")
    );

    consoleSpy.mockRestore();
  });

  it("should trigger immediately if Fides already initialized", () => {
    (window as any).Fides = {
      initialized: true,
      consent: {
        analytics: true,
        advertising: true
      }
    };

    adobe();

    expect(mockAlloy).toHaveBeenCalledWith("setConsent",
      expect.objectContaining({
        consent: expect.arrayContaining([
          expect.objectContaining({
            standard: "Adobe",
            version: "2.0"
          })
        ])
      })
    );
  });
});
```

---

## POC Summary

### Total Effort: **16 Story Points**

| Story | Points | Description |
|-------|--------|-------------|
| Story 1: Core Adobe Integration | 8 | `Fides.adobe()` with Web SDK |
| Story 2: Adobe Launch Rule Template | 3 | Copy-paste rule config |
| Story 3: POC Demo Page | 3 | Working demo with debugger |
| Story 4: Basic Smoke Tests | 2 | Minimal test coverage |
| **TOTAL** | **16** | |

### Timeline: **1 Sprint (2 weeks)**

At a typical velocity of 15-20 points per sprint with a single developer, this is achievable in **one 2-week sprint** or **5-7 working days** with focused effort.

---

## What Can We Punt?

Looking at the original 47 points, here's what we're deferring:

### Deferred to Post-POC ✂️

| Item | Points Saved | Rationale |
|------|--------------|-----------|
| **ECID Opt-In Service** | 8 pts | Legacy - most customers use Web SDK now |
| **Configurable mappings** | 5 pts | Hardcode for POC |
| **Full TypeScript definitions** | 3 pts | Minimal types sufficient |
| **Comprehensive tests** | 3 pts | Just smoke tests for POC |
| **Custom event options** | 2 pts | Simple event dispatch only |
| **Production error handling** | 3 pts | Console logs sufficient |
| **Documentation** | 3 pts | Just README for demo |
| **TOTAL DEFERRED** | **27 pts** | Save ~60% of effort |

### Could Defer Further (If Needed) ⚠️

If you need to go even leaner:

| Item | Points | Impact |
|------|--------|--------|
| Demo page | 3 pts | Could just use browser console |
| Smoke tests | 2 pts | Manual testing only |
| **MINIMUM VIABLE POC** | **11 pts** | Just Stories 1 & 2 |

This would be **5-7 business days** for one developer.

---

## Success Metrics for POC

The POC is successful if we can demonstrate:

1. ✅ **Live Demo:**
   - Show Fides consent modal
   - User opts in/out
   - Adobe Experience Platform Debugger shows consent updates
   - Adobe Analytics beacon fires/blocks correctly

2. ✅ **Code Quality:**
   - Clean, readable implementation
   - Console logs for debugging
   - Basic test coverage

3. ✅ **Customer Validation:**
   - Customer can see it working
   - Confirms approach is correct
   - Gets buy-in for full implementation

4. ✅ **Technical Validation:**
   - Confirms Adobe API works as expected
   - No unexpected blockers
   - Performance acceptable

---

## Post-POC: Path to Production

After POC is validated, the remaining work to production:

1. **Add ECID Opt-In Service** - 8 pts (for legacy customers)
2. **Make mappings configurable** - 8 pts (remove hardcoding)
3. **Add comprehensive tests** - 8 pts (full coverage)
4. **Production error handling** - 5 pts (graceful failures)
5. **Full TypeScript types** - 3 pts (complete type safety)
6. **Documentation** - 5 pts (installation guide)

**Post-POC Total: ~37 additional points** (2-3 sprints)

**Grand Total POC + Production: 53 points** (3-4 sprints)

This excludes OneTrust migration and Admin UI, which would add another ~55 points.

---

## Deliverables Checklist

### Code
- [ ] `clients/fides-js/src/integrations/adobe.ts` (POC version)
- [ ] Wire up to `init-utils.ts` and `consent-types.ts`
- [ ] Basic smoke tests

### Demo
- [ ] `clients/fides-js/examples/adobe-poc.html`
- [ ] `clients/fides-js/examples/README-adobe-poc.md`
- [ ] Working demo with Adobe Debugger

### Documentation (Minimal)
- [ ] Adobe Launch rule template (copy-paste)
- [ ] Setup instructions for demo
- [ ] Known limitations documented

### Testing
- [ ] Manual testing checklist
- [ ] Adobe Debugger verification
- [ ] Smoke tests pass in CI

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Adobe credentials not available | High | Get customer Adobe account access early |
| Adobe API behaves unexpectedly | Medium | POC will reveal issues early |
| Customer wants ECID immediately | Medium | Clear POC scope upfront |
| Hardcoded mappings confuse customer | Low | Document as temporary |

---

## Next Steps

1. **Review & Approve POC scope**
2. **Assign Story 1 (Core Integration)** - 8 pts
3. **Set up Adobe test account** - Parallel track
4. **Begin implementation** - Start with `adobe.ts`
5. **Create demo page** - Story 3
6. **Schedule demo with customer** - After Story 3 complete

**Recommended sprint:** Complete all 4 stories in single 2-week sprint for coherent demo.

---

## Questions for Team

- [ ] Do we have Adobe Experience Platform account for testing?
- [ ] Can we get customer's Adobe credentials for realistic demo?
- [ ] Is Web SDK-only sufficient, or do we need ECID in POC?
- [ ] Who will be the demo audience (customer, internal, both)?
- [ ] What's the timeline for POC demo?

---

**Document Status:** Ready for Sprint Planning
**Estimated Delivery:** 1 sprint (2 weeks) with dedicated developer
