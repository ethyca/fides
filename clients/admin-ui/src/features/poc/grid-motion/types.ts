export const CARD_IDS = [
  "card-tall",
  "card-wide-a",
  "card-wide-b",
  "card-unit-a",
  "card-unit-b",
  "card-unit-c",
  "card-unit-d",
] as const;

export type CardId = (typeof CARD_IDS)[number];

export interface CardSpan {
  cols: number;
  rows: number;
}

export interface CardSpec {
  id: CardId;
  label: string;
  collapsed: CardSpan;
  expanded: CardSpan;
  /** Lower = closer to top-right when in collapsed state. */
  collapsedOrder: number;
  /** Lower = closer to top-right when in expanded state. */
  expandedOrder: number;
}

export const CARD_SPECS: readonly CardSpec[] = [
  {
    id: "card-wide-b",
    label: "Consent Alignment",
    collapsed: { cols: 2, rows: 2 },
    expanded: { cols: 4, rows: 3 },
    collapsedOrder: 3,
    expandedOrder: 3,
  },
  {
    id: "card-unit-b",
    label: "Policy Enforcement",
    collapsed: { cols: 3, rows: 1 },
    expanded: { cols: 4, rows: 3 },
    collapsedOrder: 5,
    expandedOrder: 5,
  },
  {
    id: "card-tall",
    label: "Coverage",
    collapsed: { cols: 2, rows: 1 },
    expanded: { cols: 3, rows: 4 },
    collapsedOrder: 1,
    expandedOrder: 1,
  },
  {
    id: "card-wide-a",
    label: "Classification Health",
    collapsed: { cols: 2, rows: 1 },
    expanded: { cols: 4, rows: 3 },
    collapsedOrder: 2,
    expandedOrder: 2,
  },
  {
    id: "card-unit-a",
    label: "DSR Compliance",
    collapsed: { cols: 2, rows: 1 },
    expanded: { cols: 3, rows: 3 },
    collapsedOrder: 4,
    expandedOrder: 4,
  },
  {
    id: "card-unit-c",
    label: "AI Readiness",
    collapsed: { cols: 1, rows: 1 },
    expanded: { cols: 3, rows: 3 },
    collapsedOrder: 6,
    expandedOrder: 6,
  },
  {
    id: "card-unit-d",
    label: "Assessment Coverage",
    collapsed: { cols: 1, rows: 1 },
    expanded: { cols: 3, rows: 3 },
    collapsedOrder: 7,
    expandedOrder: 7,
  },
];
