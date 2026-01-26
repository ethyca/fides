# usePolicyToFlow Hook - Usage Example

## Overview
The `usePolicyToFlow` hook converts a PolicyV2 object into React Flow nodes and edges for visualization.

## Basic Usage

```typescript
import { usePolicyToFlow } from "./hooks";
import { PolicyV2 } from "../types";

function PolicyFlowViewer({ policy }: { policy: PolicyV2 }) {
  const { nodes, edges } = usePolicyToFlow(policy);

  return (
    <ReactFlow nodes={nodes} edges={edges} />
  );
}
```

## Example Input (PolicyV2)

```typescript
const examplePolicy: PolicyV2 = {
  id: "policy-1",
  fides_key: "gdpr_consent_policy",
  name: "GDPR Consent Policy",
  enabled: true,
  rules: [
    {
      id: "rule-1",
      name: "Marketing Data Rule",
      action: "ALLOW",
      matches: [
        {
          match_type: "taxonomy",
          target_field: "data_use",
          operator: "any",
          values: [
            { taxonomy: "data_use", element: "marketing" }
          ]
        }
      ],
      constraints: [
        {
          constraint_type: "privacy",
          configuration: {
            privacy_notice_key: "marketing_consent",
            requirement: "opt_in"
          }
        }
      ]
    },
    {
      id: "rule-2",
      name: "Essential Data Rule",
      action: "ALLOW",
      matches: [
        {
          match_type: "taxonomy",
          target_field: "data_use",
          operator: "any",
          values: [
            { taxonomy: "data_use", element: "essential" }
          ]
        }
      ],
      constraints: []
    }
  ]
};
```

## Example Output

### Rule 1 (with constraint):
**Nodes:**
- `rule-0-start` at (0, 0) - START node
- `rule-0-match-0` at (200, 0) - MATCH node for marketing data use
- `rule-0-constraint-0` at (400, 0) - CONSTRAINT node for opt_in requirement
- `rule-0-action` at (600, 0) - ACTION node (ALLOW)

**Edges:**
- START → MATCH
- MATCH → CONSTRAINT
- CONSTRAINT → ACTION

### Rule 2 (no constraints):
**Nodes:**
- `rule-1-start` at (0, 250) - START node
- `rule-1-match-0` at (200, 250) - MATCH node for essential data use
- `rule-1-action` at (400, 250) - ACTION node (ALLOW)

**Edges:**
- START → MATCH
- MATCH → ACTION

## Visual Layout

```
Rule 1:  START → MATCH → CONSTRAINT → ACTION
         (0,0)   (200,0)  (400,0)      (600,0)

Rule 2:  START → MATCH → ACTION
         (0,250) (200,250) (400,250)
```

## Complex Example with Multiple Matches

When a rule has multiple matches, a GATE node is created:

```typescript
const complexPolicy: PolicyV2 = {
  // ... basic fields
  rules: [
    {
      name: "Multi-Match Rule",
      action: "DENY",
      matches: [
        {
          match_type: "taxonomy",
          target_field: "data_use",
          operator: "any",
          values: [{ taxonomy: "data_use", element: "advertising" }]
        },
        {
          match_type: "taxonomy",
          target_field: "data_category",
          operator: "any",
          values: [{ taxonomy: "data_category", element: "user.financial" }]
        }
      ],
      constraints: [],
      on_denial_message: "This combination is not allowed"
    }
  ]
};
```

**Visual Layout:**
```
        ┌─ MATCH (advertising) ─┐
START ──┤                        ├─ GATE (AND) ─ ACTION (DENY)
        └─ MATCH (financial) ───┘
```

**Nodes:**
- `rule-0-start` at (0, 0)
- `rule-0-match-0` at (200, -40) - First match (stacked above)
- `rule-0-match-1` at (200, 40) - Second match (stacked below)
- `rule-0-gate` at (400, 0) - GATE node (centered)
- `rule-0-action` at (600, 0) - ACTION node

**Edges:**
- START → MATCH-0
- START → MATCH-1
- MATCH-0 → GATE
- MATCH-1 → GATE
- GATE → ACTION

## Node ID Conventions

- **START**: `rule-{ruleIndex}-start`
- **MATCH**: `rule-{ruleIndex}-match-{matchIndex}`
- **GATE**: `rule-{ruleIndex}-gate`
- **CONSTRAINT**: `rule-{ruleIndex}-constraint-{constraintIndex}`
- **ACTION**: `rule-{ruleIndex}-action`

## Edge ID Conventions

- Format: `edge-{sourceId}-{targetId}`
- Example: `edge-rule-0-start-rule-0-match-0`

## Performance Optimization

The hook uses `useMemo` to only recalculate nodes and edges when the policy object changes:

```typescript
const { nodes, edges } = useMemo(() => {
  // Conversion logic...
}, [policy]);
```

This ensures efficient re-renders in React Flow.

## Edge Cases Handled

1. **Empty policy**: Returns empty nodes and edges arrays
2. **No matches**: Connects START directly to constraints or action
3. **No constraints**: Connects matches (or start) directly to action
4. **Single match**: No GATE node created
5. **Multiple matches**: GATE node created and centered vertically

## Layout Constants

```typescript
const VERTICAL_SPACING = 250;              // Space between rule lanes
const HORIZONTAL_START = 0;                // X position of START
const HORIZONTAL_MATCH = 200;              // X position of MATCH nodes
const HORIZONTAL_GATE = 400;               // X position of GATE node
const HORIZONTAL_CONSTRAINT_BASE = 600;    // X position of CONSTRAINT nodes
const HORIZONTAL_ACTION_OFFSET = 200;      // Offset from last element to ACTION
const MATCH_VERTICAL_SPACING = 80;         // Space between stacked matches
const CONSTRAINT_VERTICAL_SPACING = 80;    // Space between stacked constraints
```

These can be adjusted to change the visual spacing of the flow diagram.
