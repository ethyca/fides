# Evidence Tray Redesign Proposal

## Information Architecture

### Tray Structure (Top to Bottom)

```
┌─────────────────────────────────────────┐
│ Evidence for: [Question/Section Title] │
│ [Close] [Download] [Export]            │
├─────────────────────────────────────────┤
│                                         │
│ 1. SYSTEM-DERIVED DATA                  │
│    └─ Expandable section                │
│                                         │
│ 2. HUMAN INPUT                          │
│    └─ Expandable section                │
│                                         │
│ 3. ANALYSIS & SYNTHESIS                 │
│    └─ Expandable section                │
│                                         │
└─────────────────────────────────────────┘
```

## Section 1: SYSTEM-DERIVED DATA

### Header
**Label:** "System-Derived Data"
**Description:** "Automated data points extracted from system inventory, classifications, policies, and monitoring systems."

### Default State
- **Collapsed by default** (shows count badge: "3 sources")
- **Summary line:** "3 automated data points • Last updated: 2 hours ago"

### Expanded State
Each item shows:

**Item Structure:**
- **Source Type** (badge/tag): "Data Classification" | "System Inventory" | "Policy Document" | "Compliance Monitor"
- **Value/Content** (primary text)
- **Source System** (secondary): "Fides Data Map" | "Policy Engine v2.1" | "Compliance Monitor"
- **Extracted:** [Timestamp] • **Confidence:** [Percentage if applicable]
- **Link/Reference:** [Link to source system or document]

**Example Items:**
1. **Data Classification**
   - Value: "PII, Behavioral Data"
   - Source: Fides Data Map
   - Extracted: Jan 15, 2024 14:23 UTC • Confidence: 98%
   - Reference: [View in Data Map →]

2. **System Inventory**
   - Value: "Customer Insight AI Module"
   - Source: System Inventory
   - Extracted: Jan 15, 2024 14:20 UTC
   - Reference: [View system details →]

3. **Policy Document**
   - Value: "Retention: 24 months (Section 4.2)"
   - Source: Data Retention Policy v3.1
   - Extracted: Jan 15, 2024 13:45 UTC
   - Reference: [View policy document →]

### Interaction Patterns
- **Expand/Collapse:** Show/hide all items
- **Filter:** Filter by source type (dropdown)
- **Sort:** By timestamp (newest/oldest)
- **Link out:** Direct links to source systems
- **Download:** Export individual items or all system data as JSON/CSV

---

## Section 2: HUMAN INPUT

### Header
**Label:** "Human Input"
**Description:** "Manual entries and stakeholder communications that inform this assessment."

### Default State
- **Collapsed by default** (shows count badge: "2 inputs")
- **Summary line:** "2 human inputs • Last entry: 1 hour ago"

### Expanded State
Grouped by input type:

#### Subsection 2.1: Manual Entries
**Label:** "Manual Entries"
**Description:** "Direct answers entered by assessment owners."

Each entry shows:
- **Entered by:** [Name, Role] • **Date:** [Timestamp]
- **Content:** [The actual answer/input]
- **Status:** "Verified" | "Pending Review" | "Draft"
- **Edit:** [Link to edit if user has permissions]

#### Subsection 2.2: Stakeholder Communications
**Label:** "Stakeholder Communications"
**Description:** "Conversations and requests with team members via Slack or other channels."

Each communication shows:
- **Channel:** "Slack #privacy-assessments" | "Email" | "Microsoft Teams"
- **Participants:** [List of names]
- **Thread:** [Thread title or subject]
- **Date Range:** [Start] - [End]
- **Message Count:** "12 messages"
- **Expandable Thread View:**
  - Each message: [Sender] • [Timestamp] • [Message content]
  - No avatars or chat bubbles - clean list format
  - Attribution clearly shown

**Example:**
```
Stakeholder Communication
─────────────────────────
Channel: Slack #privacy-assessments
Participants: Jack Gale, Sarah Johnson, Data Steward Team
Thread: "Customer Insight AI - Data Flow Questions"
Date Range: Jan 15, 2024 14:15 - 14:45 UTC
Message Count: 12

[Expand to view messages]
```

### Interaction Patterns
- **Expand/Collapse:** Per subsection and per thread
- **Filter:** By input type, by person, by date range
- **Search:** Full-text search across all human inputs
- **Export:** Export communications as transcript
- **Link out:** Direct links to Slack threads, emails, etc.

---

## Section 3: ANALYSIS & SYNTHESIS

### Header
**Label:** "Analysis & Synthesis"
**Description:** "Inferences and summaries generated from system data and human input."

### Default State
- **Collapsed by default** (shows count badge: "1 analysis")
- **Summary line:** "1 synthesis • Generated: 30 minutes ago"

### Expanded State
Each analysis item shows:

**Item Structure:**
- **Type:** "Summary" | "Inference" | "Risk Assessment" | "Compliance Check"
- **Generated:** [Timestamp] • **Model:** [Model version if applicable]
- **Based on:** [List of source references with links]
  - "System-Derived Data: Data Classification (3 items)"
  - "Human Input: Manual Entry by Jack Gale, Slack Thread #123"
- **Content:** [The actual analysis/summary text]
- **Confidence Score:** [If applicable, shown as percentage with explanation]
- **Regenerate:** [Button to regenerate if user has permissions]

**Example:**
```
Analysis & Synthesis
────────────────────
Type: Summary
Generated: Jan 15, 2024 15:30 UTC • Model: GPT-4-turbo (v2024.01)

Based on:
• System-Derived Data: Data Classification (3 items)
• Human Input: Manual Entry by Jack Gale (Jan 15, 14:20)
• Human Input: Slack Thread "Data Flow Questions" (12 messages)

Content:
[The summary text appears here - no anthropomorphizing language]

Confidence: 87%
[View source references →]
```

### Interaction Patterns
- **Expand/Collapse:** Show/hide analysis content
- **View Sources:** Expand to show all referenced inputs
- **Regenerate:** Request new analysis (with confirmation)
- **Download:** Export analysis as text/PDF
- **Dispute/Flag:** Mark analysis for review (if applicable)

---

## Microcopy Guidelines

### Section Headers
- Use title case: "System-Derived Data", "Human Input", "Analysis & Synthesis"
- Keep professional, neutral tone
- Avoid: "AI-generated", "Smart", "Intelligent"
- Prefer: "Automated", "System", "Analysis"

### Descriptions
- Be explicit about data sources
- Use passive voice where appropriate: "Generated from..." not "I analyzed..."
- Include timestamps in UTC with timezone
- Show attribution clearly

### Labels & Tags
- **Source Types:** "Data Classification", "System Inventory", "Policy Document", "Compliance Monitor"
- **Input Types:** "Manual Entry", "Stakeholder Communication"
- **Analysis Types:** "Summary", "Inference", "Risk Assessment", "Compliance Check"
- **Status:** "Verified", "Pending Review", "Draft", "Confirmed"

### Timestamps
- Format: "Jan 15, 2024 14:23 UTC"
- Always include timezone
- Use relative time for recent items: "2 hours ago" (with full timestamp on hover)

### Attribution
- Format: "[Name], [Role]" • "[Timestamp]"
- Example: "Jack Gale, Privacy Officer • Jan 15, 2024 14:20 UTC"
- For system sources: "[System Name] v[Version]" • "[Timestamp]"

---

## Interaction Patterns

### Expand/Collapse
- All sections collapsed by default
- Click section header to expand
- Show count badge when collapsed: "3 sources", "2 inputs", "1 analysis"
- Smooth animation (Ant Design Collapse component)

### Filtering
- Filter dropdown per section:
  - System-Derived: Filter by source type
  - Human Input: Filter by person, type, date range
  - Analysis: Filter by type, date range
- Clear filters button
- Active filters shown as tags

### Search
- Global search bar at top of tray
- Searches across all three sections
- Highlights matches
- Shows section context for each result

### Sorting
- Default: Most recent first
- Options: Oldest first, by source type, by person
- Per-section sorting

### Export
- **Download All:** Export entire evidence set as JSON/PDF
- **Download Section:** Export individual section
- **Download Item:** Export individual evidence item
- Include metadata: timestamps, attribution, source references

### Linking Out
- Direct links to:
  - Source systems (Data Map, Policy Engine, etc.)
  - Slack threads (opens in Slack)
  - Policy documents
  - System inventory entries
- External links open in new tab
- Show link icon/indicator

### Actions
- **Refresh:** Reload evidence (check for updates)
- **Request Update:** Request new stakeholder input
- **Flag for Review:** Mark evidence item for review
- **Add Note:** Add user annotation to evidence item

---

## Data Model Considerations

### Evidence Item Structure
```typescript
interface EvidenceItem {
  id: string;
  type: 'system' | 'human' | 'analysis';
  subtype: string; // e.g., 'data-classification', 'manual-entry', 'summary'
  content: string;
  source: {
    system?: string; // For system-derived
    person?: { name: string; role: string; }; // For human input
    model?: string; // For analysis
  };
  timestamp: string; // ISO 8601 UTC
  confidence?: number; // 0-100 for system/analysis items
  references?: string[]; // IDs of referenced evidence items
  metadata: {
    [key: string]: any; // Flexible metadata
  };
  links?: {
    label: string;
    url: string;
  }[];
}
```

### Section State
```typescript
interface EvidenceSection {
  type: 'system' | 'human' | 'analysis';
  items: EvidenceItem[];
  expanded: boolean;
  filters: {
    [key: string]: any;
  };
  sortBy: string;
  sortOrder: 'asc' | 'desc';
}
```

---

## Ant Design Components to Use

### Layout
- **Drawer** (existing): Right-side panel
- **Collapse**: For section expand/collapse
- **Divider**: Between sections
- **Space**: For spacing between items

### Data Display
- **List**: For evidence items
- **Descriptions**: For metadata display
- **Tag**: For source types, status badges
- **Timeline**: Optional for chronological view
- **Badge**: For counts when collapsed

### Input
- **Select**: For filtering
- **Input.Search**: For global search
- **DatePicker.RangePicker**: For date range filtering

### Actions
- **Button**: For actions (Download, Export, etc.)
- **Dropdown**: For action menus
- **Popconfirm**: For destructive actions (regenerate, delete)

### Navigation
- **Breadcrumb**: Optional for deep navigation
- **Anchor**: For section navigation if tray is long

---

## Accessibility Considerations

- All sections must be keyboard navigable
- Screen reader announcements for expand/collapse
- ARIA labels for all interactive elements
- Focus management when opening/closing sections
- High contrast for timestamps and metadata
- Clear focus indicators

---

## Performance Considerations

- Lazy load evidence items when section expands
- Virtual scrolling for long lists
- Debounce search input
- Cache evidence data
- Show loading states during fetch

---

## Notes

- This design emphasizes **transparency** and **traceability**
- No anthropomorphizing language ("I analyzed", "I found")
- Clear separation of automated vs. human vs. synthesized
- Every piece of evidence is attributable and timestamped
- Professional tone suitable for legal/audit review
- Focus on defensibility, not explainability theater
