# Adobe Purpose Mapping Configuration

## The Problem

Your Fides consent keys must be **explicitly mapped** to Adobe purposes. If the mapping doesn't match your actual consent keys, Adobe won't receive any consent updates.

### Example Error

```javascript
// Your Fides consent has these keys:
{
  "ai_analytics": true,
  "marketing": true,
  "data_sales_and_sharing": true,
  "essential": true
}

// But default mapping expects:
{
  "analytics": [...],    // ❌ Doesn't match "ai_analytics"
  "functional": [...],   // ❌ Doesn't exist in your consent
  "advertising": [...]   // ❌ Doesn't match "marketing"
}

// Result: No consent passed to Adobe! 🚨
```

## The Solution

Pass a **custom `purposeMapping`** that matches YOUR Fides consent keys:

```javascript
Fides.aep({
  purposeMapping: {
    ai_analytics: ['collect', 'measure'],        // Your key → Adobe purposes
    marketing: ['personalize', 'share'],         // Your key → Adobe purposes
    data_sales_and_sharing: ['share']            // Your key → Adobe purposes
  },
  debug: true  // Shows mapping in console
});
```

## Adobe Purpose Reference

Adobe has 4 standard consent purposes:

| Adobe Purpose | Description | Maps to ECID Category |
|---------------|-------------|----------------------|
| `collect` | Collect data | Analytics (`aa`) |
| `measure` | Measure/analyze data | Analytics (`aa`) |
| `personalize` | Personalize content | Target (`target`) |
| `share` | Share with 3rd parties | Audience Manager (`aam`) |

## Common Mapping Patterns

### Pattern 1: Standard Fides Keys (Default)

```javascript
// If your consent keys are: analytics, functional, advertising
Fides.aep();  // No config needed, uses defaults
```

### Pattern 2: Custom Keys (Your Case)

```javascript
// If your consent keys are: ai_analytics, marketing, data_sales_and_sharing
Fides.aep({
  purposeMapping: {
    ai_analytics: ['collect', 'measure'],
    marketing: ['personalize', 'share'],
    data_sales_and_sharing: ['share']
  },
  debug: true
});
```

### Pattern 3: OneTrust Migration Keys

```javascript
// If migrating from OneTrust with C0001-style keys
Fides.aep({
  purposeMapping: {
    C0001: ['collect', 'measure'],           // Strictly Necessary
    C0002: ['personalize'],                   // Performance/Functional
    C0003: ['personalize', 'share'],         // Targeting/Advertising
    C0004: ['collect', 'share']              // Social Media
  }
});
```

### Pattern 4: Granular Purposes

```javascript
// If you have very specific consent categories
Fides.aep({
  purposeMapping: {
    analytics_cookies: ['collect', 'measure'],
    marketing_cookies: ['personalize', 'share'],
    third_party_ads: ['share'],
    personalization: ['personalize'],
    performance: ['measure']
  }
});
```

## Debug Your Mapping

### Step 1: Enable Debug Mode

```javascript
const aep = Fides.aep({
  purposeMapping: { /* your mapping */ },
  debug: true
});
```

### Step 2: Check Console Logs

When consent updates, you'll see:

```
[Fides Adobe] Pushing consent to Adobe: {
  ai_analytics: true,
  marketing: true,
  data_sales_and_sharing: true,
  essential: true
}

[Fides Adobe] Purpose mapping: {
  fidesConsentKeys: ['ai_analytics', 'marketing', 'data_sales_and_sharing', 'essential'],
  mappingKeys: ['ai_analytics', 'marketing', 'data_sales_and_sharing'],
  matchedKeys: ['ai_analytics', 'marketing', 'data_sales_and_sharing'],
  unmatchedKeys: ['essential'],
  resultingPurposes: {
    collect: 'in',
    measure: 'in',
    personalize: 'in',
    share: 'in'
  }
}
```

### Step 3: Verify Adobe Received It

```javascript
// Check what Adobe has
const state = aep.consent();
console.log(state.summary);
// Should show: { analytics: true, personalization: true, advertising: true }
```

### Step 4: Warning Messages

If keys don't match, you'll see:

```
⚠️ [Fides Adobe] Found 4 consent key(s) not in purposeMapping:
   ['ai_analytics', 'marketing', 'data_sales_and_sharing', 'essential']

   To map these keys, pass a custom purposeMapping option to Fides.aep()
```

## Configuration Workflow

### 1. Discover Your Consent Keys

```javascript
// Check what keys your Fides instance uses
console.log(Object.keys(window.Fides.consent));
// Example output: ['ai_analytics', 'marketing', 'data_sales_and_sharing', 'essential']
```

### 2. Design Your Mapping

Map each key to Adobe purposes based on what the key represents:

```javascript
const purposeMapping = {
  // Analytics → collect + measure
  ai_analytics: ['collect', 'measure'],

  // Marketing/Advertising → personalize + share
  marketing: ['personalize', 'share'],

  // Data Sales → share only
  data_sales_and_sharing: ['share'],

  // Essential/Required → usually not mapped to optional Adobe purposes
  // (skip this or map if needed)
};
```

### 3. Test with Debug Mode

```javascript
const aep = Fides.aep({
  purposeMapping,
  debug: true
});

// Make a consent change in Fides modal
// Watch console for "[Fides Adobe]" logs

// Verify Adobe got it
setTimeout(() => {
  console.log('Adobe consent:', aep.consent().summary);
}, 2000);
```

### 4. Verify in Adobe Debugger

1. Install [Adobe Experience Platform Debugger](https://chrome.google.com/webstore/detail/adobe-experience-platform/bfnnokhpnncpkdmbokanobigaccjkpob)
2. Open debugger → Consent tab
3. Confirm consent values match your expectations

### 5. Deploy

Once verified, remove `debug: true` for production:

```javascript
Fides.aep({
  purposeMapping: {
    ai_analytics: ['collect', 'measure'],
    marketing: ['personalize', 'share'],
    data_sales_and_sharing: ['share']
  }
});
```

## ECID Category Mapping

The `purposeMapping` automatically translates to ECID Opt-In Service categories:

| Adobe Purpose(s) | ECID Category | Adobe Product |
|-----------------|---------------|---------------|
| `collect`, `measure` | `aa` | Adobe Analytics |
| `personalize` | `target` | Adobe Target |
| `share` | `aam` | Audience Manager |

**Example:**
```javascript
purposeMapping: {
  ai_analytics: ['collect', 'measure'],  // → ECID 'aa' approved
  marketing: ['personalize', 'share']     // → ECID 'target' + 'aam' approved
}
```

Result in ECID:
```javascript
aep.consent().ecidOptIn
// {
//   configured: true,
//   aa: true,       // ✅ from 'collect'/'measure'
//   target: true,   // ✅ from 'personalize'
//   aam: true       // ✅ from 'share'
// }
```

## Troubleshooting

### Issue: No consent changes in Adobe

**Symptom:**
```javascript
aep.consent().summary
// { analytics: false, personalization: false, advertising: false }
// (Even after accepting consent)
```

**Fix:**
Check console for unmatched keys warning. Add custom `purposeMapping`.

---

### Issue: Some keys work, others don't

**Symptom:**
```
[Fides Adobe] Found 2 consent key(s) not in purposeMapping: ['ai_analytics', 'data_sales_and_sharing']
```

**Fix:**
Your mapping is incomplete. Add the missing keys:
```javascript
purposeMapping: {
  marketing: ['personalize', 'share'],        // ✅ Already mapped
  ai_analytics: ['collect', 'measure'],       // ➕ Add this
  data_sales_and_sharing: ['share']           // ➕ Add this
}
```

---

### Issue: Not sure which purposes to use

**Answer:**
- **Analytics/Measurement** → `collect`, `measure`
- **Marketing/Advertising** → `personalize`, `share`
- **Personalization** → `personalize`
- **Data Sales/3rd Party** → `share`
- **Essential/Required** → Usually not mapped (leave out)

---

### Issue: Debug logs not showing

**Fix:**
Make sure you passed `debug: true`:
```javascript
Fides.aep({ purposeMapping: {...}, debug: true });
```

## Example: Full Setup for Your Case

Based on your consent keys: `ai_analytics`, `marketing`, `data_sales_and_sharing`, `essential`

```html
<head>
  <!-- Load Fides.js -->
  <script src="/api/fides.js"></script>

  <!-- Configure Adobe integration with YOUR keys -->
  <script>
    window.Fides.aep({
      purposeMapping: {
        // Map YOUR Fides keys → Adobe purposes
        ai_analytics: ['collect', 'measure'],        // Analytics tracking
        marketing: ['personalize', 'share'],         // Marketing & ads
        data_sales_and_sharing: ['share']            // 3rd party sharing
        // Note: 'essential' not mapped (always required)
      },
      debug: true  // Remove in production
    });
  </script>

  <!-- Load Adobe Launch -->
  <script src="https://assets.adobedtm.com/YOUR-PROPERTY/launch.min.js"></script>
</head>
```

**Expected Result:**

```javascript
// After accepting all consent:
window.Fides.consent
// {
//   ai_analytics: true,
//   marketing: true,
//   data_sales_and_sharing: true,
//   essential: true
// }

const aep = window.Fides.aep();
aep.consent().summary
// ✅ { analytics: true, personalization: true, advertising: true }

aep.consent().ecidOptIn
// ✅ { configured: true, aa: true, target: true, aam: true }
```

## Admin UI Configuration (Future)

In the future, this mapping will be configurable in Fides Admin UI:

**Adobe Experience Platform Destination Settings:**
- Notice: "AI Analytics" → Adobe Purposes: `collect`, `measure`
- Notice: "Marketing" → Adobe Purposes: `personalize`, `share`
- Notice: "Data Sales" → Adobe Purposes: `share`

For now, configure in code via `purposeMapping`.
