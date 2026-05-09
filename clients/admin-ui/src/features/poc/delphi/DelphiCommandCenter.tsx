import { AnimatePresence, motion } from "framer-motion";
import { useMemo, useState } from "react";

import { CardViz } from "./DelphiCardViz";

/* -------------------------------------------------------------------------- */
/* Tokens                                                                      */
/* -------------------------------------------------------------------------- */

const CORINTH_BG = "#FAFAFA";
const SHADE = "#CDD2D3";
const PARCHMENT = "#FFFFFF";
const CORINTH = "#2B2D34";
const TERRACOTTA = "#B96E46";
const OLIVE = "#92977D";

const INK = CORINTH;
const INK_MUTED = "rgba(43, 45, 52, 0.58)";
const INK_FAINT = "rgba(43, 45, 52, 0.34)";
const INK_HAIRLINE = "rgba(43, 45, 52, 0.10)";
const INK_DOT = "rgba(43, 45, 52, 0.16)";

const SERIF = `'Tiempos Headline', 'Charter', Georgia, 'Times New Roman', serif`;
const SANS = `'Basier Square', 'Inter', system-ui, -apple-system, sans-serif`;
const MONO = `'Basier Square Mono', ui-monospace, SFMono-Regular, monospace`;

/* -------------------------------------------------------------------------- */
/* Domain                                                                      */
/* -------------------------------------------------------------------------- */

type Status = "good" | "fair" | "attention";
type DimensionId =
  | "coverage"
  | "classification"
  | "consent"
  | "dsr"
  | "policy"
  | "ai"
  | "assessment";

type Dimension = {
  id: DimensionId;
  name: string;
  score: number;
  weight: number;
  status: Status;
  delta7d: number;
  trend: number[];
  driver: string;
  licensed: boolean;
};

const DIMENSIONS: Dimension[] = [
  {
    id: "coverage",
    name: "Coverage",
    score: 92,
    weight: 20,
    status: "good",
    delta7d: 1,
    trend: [88, 89, 90, 90, 91, 92, 92],
    driver: "6 new data sources detected",
    licensed: true,
  },
  {
    id: "classification",
    name: "Classification",
    score: 71,
    weight: 15,
    status: "fair",
    delta7d: -2,
    trend: [73, 73, 72, 72, 72, 71, 71],
    driver: "42 classification gaps",
    licensed: true,
  },
  {
    id: "consent",
    name: "Consent",
    score: 64,
    weight: 15,
    status: "fair",
    delta7d: -1,
    trend: [65, 65, 64, 64, 65, 64, 64],
    driver: "Low confidence on 18 tags",
    licensed: false,
  },
  {
    id: "dsr",
    name: "DSR",
    score: 76,
    weight: 15,
    status: "attention",
    delta7d: -4,
    trend: [80, 79, 78, 78, 77, 76, 76],
    driver: "23 overdue requests",
    licensed: true,
  },
  {
    id: "policy",
    name: "Policy Enforcement",
    score: 58,
    weight: 15,
    status: "attention",
    delta7d: -3,
    trend: [61, 61, 60, 59, 59, 58, 58],
    driver: "7 retention violations",
    licensed: true,
  },
  {
    id: "ai",
    name: "AI Readiness",
    score: 81,
    weight: 10,
    status: "good",
    delta7d: 2,
    trend: [79, 79, 80, 80, 80, 81, 81],
    driver: "3 new AI systems detected",
    licensed: true,
  },
  {
    id: "assessment",
    name: "Assessment Coverage",
    score: 87,
    weight: 10,
    status: "good",
    delta7d: 0,
    trend: [87, 87, 87, 87, 87, 87, 87],
    driver: "12 assessments completed",
    licensed: false,
  },
];

const OVERALL_SCORE = 84;
const LICENSED_DIMENSIONS: DimensionId[] = [
  "coverage",
  "classification",
  "dsr",
  "policy",
  "ai",
];

const statusColor = (s: Status): string => {
  if (s === "good") return OLIVE;
  if (s === "attention") return TERRACOTTA;
  return "rgba(43, 45, 52, 0.42)";
};

const statusLabel = (s: Status): string => {
  if (s === "good") return "Good";
  if (s === "attention") return "Attention";
  return "Fair";
};

/* -------------------------------------------------------------------------- */
/* Signals                                                                     */
/* -------------------------------------------------------------------------- */

type CardShape = "wide" | "tall" | "square";

type SignalCard = {
  id: string;
  title: string;
  count: string;
  unit?: string;
  priority: "high" | "med" | "low";
  shape: CardShape;
  summary: string;
  expanded: string;
  rows: { label: string; meta: string }[];
  primary: string;
  secondary: string;
};

const SIGNALS: Partial<Record<DimensionId, SignalCard[]>> = {
  dsr: [
    {
      id: "dsr-sla",
      title: "Requests at SLA Risk",
      count: "23",
      priority: "high",
      shape: "wide",
      summary: "Within 48h of statutory breach.",
      expanded:
        "Twenty-three subject requests are within 48 hours of breach. Most originate from the Acme connector queue, where verification has stalled.",
      rows: [
        { label: "Erasure · acme.com", meta: "due in 14h" },
        { label: "Access · contoso.io", meta: "due in 18h" },
        { label: "Erasure · datadyne.co", meta: "due in 22h" },
        { label: "Access · initech.com", meta: "due in 28h" },
      ],
      primary: "Process requests",
      secondary: "Reassign owners",
    },
    {
      id: "dsr-failed",
      title: "Failed Fulfillment Steps",
      count: "5",
      priority: "med",
      shape: "tall",
      summary: "Connector errors during fulfillment.",
      expanded:
        "Five fulfillment steps failed in the last 48 hours, concentrated in Postgres deletions and HubSpot lookups.",
      rows: [
        { label: "Postgres · users", meta: "FK constraint" },
        { label: "HubSpot · contacts", meta: "401 unauthorized" },
        { label: "Mixpanel · profiles", meta: "rate limited" },
      ],
      primary: "Retry steps",
      secondary: "Inspect connector",
    },
    {
      id: "dsr-escalations",
      title: "Subject Escalations",
      count: "3",
      priority: "med",
      shape: "tall",
      summary: "Refiles after rejected responses.",
      expanded:
        "Three subjects have escalated after a prior response was rejected. All three relate to the same retention policy on analytics events.",
      rows: [
        { label: "Refile · analytics events", meta: "3 subjects" },
      ],
      primary: "Review responses",
      secondary: "Open thread",
    },
    {
      id: "dsr-stuck",
      title: "Stuck Requests",
      count: "8",
      priority: "med",
      shape: "wide",
      summary: "Awaiting verification or downstream response.",
      expanded:
        "Eight requests are stalled on identity verification or unresponsive systems. The Salesforce connector has not acknowledged in 36 hours.",
      rows: [
        { label: "Salesforce connector", meta: "no response 36h" },
        { label: "Identity verification", meta: "5 pending" },
        { label: "Snowflake erasure", meta: "retry queued" },
      ],
      primary: "Resolve blockers",
      secondary: "Notify subjects",
    },
    {
      id: "dsr-verify",
      title: "Identity Verification Queue",
      count: "14",
      priority: "low",
      shape: "wide",
      summary: "Awaiting reviewer approval.",
      expanded:
        "Fourteen subjects need manual verification review. Average wait is 19 hours, above the 12h target.",
      rows: [
        { label: "Manual review queue", meta: "14 pending" },
        { label: "Average wait", meta: "19h" },
      ],
      primary: "Open queue",
      secondary: "Adjust policy",
    },
  ],
  policy: [
    {
      id: "pol-retention",
      title: "Retention Violations",
      count: "7",
      priority: "high",
      shape: "tall",
      summary: "Records past stated retention.",
      expanded:
        "Seven datasets contain records that have exceeded their declared retention. The largest is analytics_events with 1.2M rows past policy.",
      rows: [
        { label: "analytics_events", meta: "1.2M rows" },
        { label: "session_logs", meta: "184k rows" },
        { label: "support_tickets", meta: "9k rows" },
      ],
      primary: "Schedule deletion",
      secondary: "Adjust policy",
    },
    {
      id: "pol-ai",
      title: "AI Policy Violations",
      count: "2",
      priority: "high",
      shape: "tall",
      summary: "Models violating use policy.",
      expanded:
        "Two model deployments have triggered policy violations: one for prohibited input categories, one for missing impact assessment.",
      rows: [
        { label: "support-bot v3", meta: "missing IA" },
        { label: "fraud-classifier", meta: "prohibited input" },
      ],
      primary: "Open violations",
      secondary: "Notify owner",
    },
    {
      id: "pol-sensitive",
      title: "Unexpected Sensitive Data",
      count: "11",
      priority: "high",
      shape: "wide",
      summary: "Sensitive fields outside expected systems.",
      expanded:
        "Eleven fields detected as sensitive outside the systems where they are permitted by data map.",
      rows: [
        { label: "logs.auth_payload", meta: "PII detected" },
        { label: "events.props.email", meta: "Email" },
        { label: "tmp.exports.csv", meta: "SSN-like" },
      ],
      primary: "Quarantine fields",
      secondary: "Review map",
    },
    {
      id: "pol-sla",
      title: "SLA Breaches",
      count: "7",
      priority: "med",
      shape: "wide",
      summary: "Workflows past SLA.",
      expanded:
        "Seven governance workflows have crossed their SLA, mostly approval queues for new integrations.",
      rows: [
        { label: "Integration approvals", meta: "5 over SLA" },
        { label: "Risk reviews", meta: "2 over SLA" },
      ],
      primary: "Reassign",
      secondary: "Escalate",
    },
    {
      id: "pol-web",
      title: "Web Monitor Policy Breaches",
      count: "5",
      priority: "med",
      shape: "wide",
      summary: "Tags running outside consent.",
      expanded:
        "Five third-party tags fired before consent on at least one production page. Two are ad-network pixels.",
      rows: [
        { label: "/checkout · meta-pixel", meta: "pre-consent" },
        { label: "/blog · hotjar", meta: "pre-consent" },
        { label: "/pricing · linkedin", meta: "pre-consent" },
      ],
      primary: "Block tags",
      secondary: "Open report",
    },
  ],
  coverage: [
    {
      id: "cov-new",
      title: "New Data Sources",
      count: "6",
      priority: "med",
      shape: "wide",
      summary: "Detected since last scan.",
      expanded:
        "Six new data sources were observed in the last 7 days, including two unmanaged S3 buckets surfaced by network logs.",
      rows: [
        { label: "s3://acme-eu-prod-logs", meta: "unmanaged" },
        { label: "postgres://reporting-3", meta: "new" },
        { label: "snowflake://growth_db", meta: "new" },
      ],
      primary: "Add to inventory",
      secondary: "Assign owner",
    },
    {
      id: "cov-conn",
      title: "Integration Health",
      count: "2",
      unit: "failing",
      priority: "high",
      shape: "tall",
      summary: "Connectors degraded or failing.",
      expanded:
        "Two connectors are failing health checks, blocking inventory and DSR fulfillment downstream.",
      rows: [
        { label: "salesforce-prod", meta: "auth expired" },
        { label: "stripe-eu", meta: "rate limited" },
      ],
      primary: "Reauthorize",
      secondary: "Open logs",
    },
    {
      id: "cov-fulfill",
      title: "Fulfillment Connector Coverage",
      count: "91",
      unit: "%",
      priority: "low",
      shape: "square",
      summary: "Of inventory reachable for DSR.",
      expanded:
        "Ninety-one percent of inventoried datasets are reachable through fulfillment connectors. The remaining 9% are mostly archival.",
      rows: [
        { label: "Reachable", meta: "91%" },
        { label: "Unreachable archival", meta: "8%" },
        { label: "Unreachable other", meta: "1%" },
      ],
      primary: "Improve coverage",
      secondary: "Export gap list",
    },
    {
      id: "cov-stale",
      title: "Stale Inventory",
      count: "4",
      priority: "low",
      shape: "tall",
      summary: "Not scanned in 30+ days.",
      expanded:
        "Four sources have not been scanned in over 30 days. Two are flagged as in-scope for upcoming audits.",
      rows: [
        { label: "bigquery://eu-marketing", meta: "47d" },
        { label: "mongo://crm-archive", meta: "62d" },
      ],
      primary: "Rescan now",
      secondary: "Mark deprecated",
    },
    {
      id: "cov-drift",
      title: "Schema Drift",
      count: "18",
      unit: "fields",
      priority: "med",
      shape: "wide",
      summary: "New fields and tables since last scan.",
      expanded:
        "Eighteen new fields and three new tables appeared in monitored schemas without classification.",
      rows: [
        { label: "users.signup_geo", meta: "unclassified" },
        { label: "orders.tax_id", meta: "unclassified" },
        { label: "events_v2", meta: "new table" },
      ],
      primary: "Classify drift",
      secondary: "View diff",
    },
  ],
  classification: [
    {
      id: "cls-gaps",
      title: "Classification Gaps",
      count: "42",
      priority: "high",
      shape: "wide",
      summary: "Fields without a category.",
      expanded:
        "Forty-two fields lack a classification across the data map. The bulk live in marketing and product analytics tables.",
      rows: [
        { label: "marketing.lead_meta", meta: "12 fields" },
        { label: "product.events", meta: "18 fields" },
        { label: "support.tickets", meta: "12 fields" },
      ],
      primary: "Run classifier",
      secondary: "Assign reviewer",
    },
    {
      id: "cls-low",
      title: "Low Confidence Tags",
      count: "18",
      priority: "med",
      shape: "square",
      summary: "Below review threshold.",
      expanded:
        "Eighteen automated classifications are below 0.7 confidence and queued for review.",
      rows: [
        { label: "users.locale_hint", meta: "0.61" },
        { label: "orders.notes", meta: "0.58" },
        { label: "support.body", meta: "0.66" },
      ],
      primary: "Open review",
      secondary: "Adjust threshold",
    },
    {
      id: "cls-sensitive",
      title: "Sensitive Data Unexpected",
      count: "11",
      priority: "high",
      shape: "wide",
      summary: "Sensitive content in non-sensitive systems.",
      expanded:
        "Eleven sensitive fields appear in datasets that the data map does not designate sensitive.",
      rows: [
        { label: "logs.auth_payload", meta: "PII" },
        { label: "events.props.email", meta: "Email" },
      ],
      primary: "Quarantine",
      secondary: "Update map",
    },
    {
      id: "cls-lineage",
      title: "Lineage Changes",
      count: "9",
      priority: "low",
      shape: "wide",
      summary: "Upstream sources changed.",
      expanded:
        "Nine downstream tables now derive from new upstream sources. Classification needs revalidation.",
      rows: [
        { label: "dim_users", meta: "new upstream" },
        { label: "fct_orders", meta: "new upstream" },
      ],
      primary: "Revalidate",
      secondary: "View graph",
    },
    {
      id: "cls-new",
      title: "New Fields Needing Classification",
      count: "18",
      priority: "med",
      shape: "wide",
      summary: "Discovered since last scan.",
      expanded:
        "Eighteen newly observed fields await classification. Half originate in growth product schemas.",
      rows: [
        { label: "growth.referrer_hash", meta: "new" },
        { label: "growth.campaign_meta", meta: "new" },
      ],
      primary: "Run classifier",
      secondary: "Defer",
    },
  ],
  ai: [
    {
      id: "ai-new",
      title: "New AI Systems Detected",
      count: "3",
      priority: "med",
      shape: "wide",
      summary: "Discovered through code or vendor signals.",
      expanded:
        "Three new AI systems entered the inventory: two internal services and one third-party vendor capability.",
      rows: [
        { label: "support-bot v3", meta: "internal" },
        { label: "lead-scoring", meta: "internal" },
        { label: "Zendesk · suggest", meta: "vendor" },
      ],
      primary: "Run intake",
      secondary: "Assign owner",
    },
    {
      id: "ai-drift",
      title: "Risk Drift",
      count: "4",
      priority: "high",
      shape: "wide",
      summary: "Tier change since last review.",
      expanded:
        "Four systems have moved tier upward since their last review, including two now in high-risk.",
      rows: [
        { label: "fraud-classifier", meta: "→ high" },
        { label: "pricing-optimizer", meta: "→ high" },
      ],
      primary: "Reassess",
      secondary: "Notify owners",
    },
    {
      id: "ai-vendor",
      title: "Vendor AI Changes",
      count: "2",
      priority: "med",
      shape: "tall",
      summary: "Vendor terms or capabilities updated.",
      expanded:
        "Two vendors changed AI usage or training-data terms within the last 14 days.",
      rows: [
        { label: "Zendesk", meta: "policy update" },
        { label: "Notion", meta: "new AI feature" },
      ],
      primary: "Review terms",
      secondary: "Flag for legal",
    },
    {
      id: "ai-training",
      title: "Training Data Exposure",
      count: "1",
      priority: "high",
      shape: "square",
      summary: "Sensitive data in training set.",
      expanded:
        "One training dataset contains records flagged as sensitive without an explicit lawful basis.",
      rows: [
        { label: "support-bot · finetune-2", meta: "sensitive" },
      ],
      primary: "Quarantine dataset",
      secondary: "Document basis",
    },
    {
      id: "ai-fw",
      title: "Framework Readiness Drift",
      count: "6",
      priority: "low",
      shape: "wide",
      summary: "EU AI Act controls without evidence.",
      expanded:
        "Six controls under EU AI Act mapping have not been refreshed in 90 days.",
      rows: [
        { label: "Art.10 · data governance", meta: "stale" },
        { label: "Art.13 · transparency", meta: "stale" },
      ],
      primary: "Refresh evidence",
      secondary: "Open framework",
    },
  ],
  consent: [
    {
      id: "con-drift",
      title: "Consent Rate Drift",
      count: "−4%",
      priority: "high",
      shape: "wide",
      summary: "Acceptance rate dropped across jurisdictions.",
      expanded:
        "Acceptance rate fell across the EU and UK over the last 30 days. The largest drop is DE (−7%), aligned with a banner copy change shipped May 1.",
      rows: [
        { label: "DE", meta: "−7%" },
        { label: "FR", meta: "−4%" },
        { label: "UK", meta: "−2%" },
      ],
      primary: "Review banner",
      secondary: "Compare versions",
    },
    {
      id: "con-gaps",
      title: "Consent Coverage Gaps",
      count: "4",
      unit: "regions",
      priority: "high",
      shape: "tall",
      summary: "Jurisdictions without compliant consent.",
      expanded:
        "Four regions are missing or running stale consent surfaces. BR has no banner deployed; AU is on a notice version pulled in March.",
      rows: [
        { label: "BR · no banner", meta: "missing" },
        { label: "IN · partial coverage", meta: "62%" },
        { label: "AU · notice v2.1", meta: "stale 71d" },
      ],
      primary: "Deploy coverage",
      secondary: "Open jurisdictions",
    },
    {
      id: "con-regulatory",
      title: "Regulatory Drift",
      count: "2",
      priority: "med",
      shape: "tall",
      summary: "Recent regulator guidance affecting consent.",
      expanded:
        "Two regulator updates in the last 14 days touch consent obligations. CCPA enforcement note clarifies dark-pattern definitions; EU AI Act guidance adds consent requirements for biometric inference.",
      rows: [
        { label: "California · CCPA dark patterns", meta: "May 6" },
        { label: "EU · AI Act biometric consent", meta: "May 2" },
      ],
      primary: "Open guidance",
      secondary: "Notify legal",
    },
    {
      id: "con-records",
      title: "Records Anomalies",
      count: "14",
      priority: "med",
      shape: "wide",
      summary: "Consent records failing integrity checks.",
      expanded:
        "Fourteen consent records fail integrity checks: timestamp drift, missing version stamps, or provenance gaps. Above the 10/day baseline.",
      rows: [
        { label: "Timestamp drift", meta: "8" },
        { label: "Missing version stamp", meta: "4" },
        { label: "Provenance gap", meta: "2" },
      ],
      primary: "Open audit",
      secondary: "Export records",
    },
    {
      id: "con-notice",
      title: "Notice Version Coverage",
      count: "87",
      unit: "%",
      priority: "low",
      shape: "square",
      summary: "Of surfaces on the current notice version.",
      expanded:
        "Eighty-seven percent of consent surfaces serve the latest notice version. The remaining 13% are concentrated on legacy mobile builds awaiting forced update.",
      rows: [
        { label: "Current version", meta: "87%" },
        { label: "Legacy mobile", meta: "11%" },
        { label: "Other stale", meta: "2%" },
      ],
      primary: "Force update",
      secondary: "View diff",
    },
    {
      id: "con-revocation",
      title: "Preference Revocation Surge",
      count: "3.2x",
      priority: "high",
      shape: "wide",
      summary: "Revocations vs. 30-day baseline.",
      expanded:
        "Revocations are 3.2x the 30-day baseline today. Concentrated on marketing and analytics purposes following last week's policy update email campaign.",
      rows: [
        { label: "Marketing purpose", meta: "62% of revocations" },
        { label: "Analytics purpose", meta: "28%" },
        { label: "Personalization", meta: "10%" },
      ],
      primary: "Open campaign",
      secondary: "Notify owners",
    },
  ],
  assessment: [
    {
      id: "asm-pending",
      title: "Pending Assessments",
      count: "8",
      unit: "open",
      priority: "high",
      shape: "wide",
      summary: "Awaiting assessor review.",
      expanded:
        "Eight assessments are awaiting reviewer pickup. Average wait is 4.5 days; the oldest is 6 days, past the 5-day SLA.",
      rows: [
        { label: "Vendor · Anthropic intake", meta: "6d" },
        { label: "AI · pricing-optimizer", meta: "4d" },
        { label: "Vendor · Linear intake", meta: "3d" },
      ],
      primary: "Open queue",
      secondary: "Reassign reviewers",
    },
    {
      id: "asm-stale",
      title: "Stale Assessments",
      count: "5",
      priority: "med",
      shape: "tall",
      summary: "Past their reassessment date.",
      expanded:
        "Five assessments are past their declared reassessment date. The oldest (Marketing AI) hasn't been refreshed in 124 days.",
      rows: [
        { label: "Marketing AI", meta: "124d" },
        { label: "Vendor · Notion", meta: "96d" },
        { label: "Ad targeting", meta: "72d" },
      ],
      primary: "Schedule reassess",
      secondary: "Notify owners",
    },
    {
      id: "asm-dpia",
      title: "High-Risk Without DPIA",
      count: "2",
      priority: "high",
      shape: "tall",
      summary: "High-risk systems missing impact assessment.",
      expanded:
        "Two systems classified high-risk are operating without a current DPIA. Both require remediation before the next audit cycle.",
      rows: [
        { label: "fraud-classifier", meta: "high-risk" },
        { label: "lead-gen scoring", meta: "high-risk" },
      ],
      primary: "Initiate DPIA",
      secondary: "Notify owners",
    },
    {
      id: "asm-coverage",
      title: "Coverage Proportion",
      count: "73",
      unit: "%",
      priority: "low",
      shape: "square",
      summary: "Of in-scope systems with current assessment.",
      expanded:
        "Seventy-three percent of in-scope systems are covered by a current assessment. The 27% gap is concentrated in recently inventoried vendor integrations.",
      rows: [
        { label: "Covered", meta: "73%" },
        { label: "Vendor gap", meta: "21%" },
        { label: "Internal gap", meta: "6%" },
      ],
      primary: "Improve coverage",
      secondary: "Export gap list",
    },
    {
      id: "asm-new",
      title: "New AI Awaiting Assessment",
      count: "5",
      priority: "med",
      shape: "wide",
      summary: "Detected systems queued for intake.",
      expanded:
        "Five newly detected AI systems are queued for assessment intake. Three are vendor capabilities; two are internal services.",
      rows: [
        { label: "Vendor · Zendesk Suggest", meta: "vendor" },
        { label: "Vendor · Notion AI", meta: "vendor" },
        { label: "support-bot v3", meta: "internal" },
      ],
      primary: "Run intake",
      secondary: "Assign owner",
    },
    {
      id: "asm-due",
      title: "Reassessment Due Window",
      count: "6",
      unit: "due",
      priority: "med",
      shape: "wide",
      summary: "Assessments due in the next 30 days.",
      expanded:
        "Six assessments fall within the next 30 days. Two are inside the 7-day attention window and require scheduling now.",
      rows: [
        { label: "fraud-classifier reassess", meta: "5d" },
        { label: "Vendor · Datadog", meta: "9d" },
        { label: "support-bot v3", meta: "14d" },
      ],
      primary: "Schedule reassessments",
      secondary: "Notify owners",
    },
  ],
};

const PROMPT_BY_DIMENSION: Record<DimensionId, string> = {
  coverage: "What changed in our data inventory this week?",
  classification: "Which datasets are missing classification?",
  consent: "Where is consent coverage lowest right now?",
  dsr: "Why did DSR decline this week?",
  policy: "Which policies are seeing the most violations?",
  ai: "What new AI systems were detected, and how risky are they?",
  assessment: "Which assessments are overdue?",
};

const NARRATIVE_BY_DIMENSION: Record<DimensionId, string> = {
  coverage:
    "Coverage is strong at 92, up one point this week. Six new data sources were detected; most are managed, but two need owners.",
  classification:
    "Classification is at 71 and slipping. Forty-two fields are uncategorized and 18 tags are below review threshold.",
  consent:
    "Consent is at 64. Recent web monitor signals show pre-consent tag fires on three pages.",
  dsr:
    "DSR fell four points to 76. Twenty-three requests are within 48 hours of SLA breach, concentrated in the Acme connector queue.",
  policy:
    "Policy enforcement is at 58 and trending down. Seven retention violations and eleven unexpected sensitive findings need review.",
  ai:
    "AI Readiness is at 81. Three new AI systems were detected this week, and four existing systems drifted upward in risk tier.",
  assessment:
    "Assessment coverage holds at 87. Twelve assessments completed this week; none are overdue.",
};

/* -------------------------------------------------------------------------- */
/* Geometry                                                                    */
/* -------------------------------------------------------------------------- */

const SIZE = 480;
const CX = SIZE / 2;
const CY = SIZE / 2;
const INNER_R = 60;
const OUTER_R = 180;
const LABEL_R = OUTER_R + 42;
const ARC_GAP_DEG = 2.4;

const polar = (cx: number, cy: number, r: number, deg: number) => {
  const a = ((deg - 90) * Math.PI) / 180;
  return [cx + r * Math.cos(a), cy + r * Math.sin(a)] as const;
};

const arcPath = (cx: number, cy: number, r: number, a1: number, a2: number) => {
  const [x1, y1] = polar(cx, cy, r, a1);
  const [x2, y2] = polar(cx, cy, r, a2);
  const large = a2 - a1 > 180 ? 1 : 0;
  return `M ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2}`;
};

const wedgePath = (
  cx: number,
  cy: number,
  rIn: number,
  rOut: number,
  a1: number,
  a2: number,
) => {
  const [x1o, y1o] = polar(cx, cy, rOut, a1);
  const [x2o, y2o] = polar(cx, cy, rOut, a2);
  const [x1i, y1i] = polar(cx, cy, rIn, a1);
  const [x2i, y2i] = polar(cx, cy, rIn, a2);
  const large = a2 - a1 > 180 ? 1 : 0;
  return [
    `M ${x1o} ${y1o}`,
    `A ${rOut} ${rOut} 0 ${large} 1 ${x2o} ${y2o}`,
    `L ${x2i} ${y2i}`,
    `A ${rIn} ${rIn} 0 ${large} 0 ${x1i} ${y1i}`,
    "Z",
  ].join(" ");
};

type Slice = Dimension & {
  startAngle: number;
  endAngle: number;
  midAngle: number;
  scoreRadius: number;
};

const buildSlices = (): Slice[] => {
  const total = DIMENSIONS.reduce((s, d) => s + d.weight, 0);
  const firstSpan = (DIMENSIONS[0].weight / total) * 360;
  let cursor = -firstSpan / 2;
  return DIMENSIONS.map((d) => {
    const span = (d.weight / total) * 360;
    const startAngle = cursor;
    const endAngle = cursor + span;
    cursor = endAngle;
    const midAngle = (startAngle + endAngle) / 2;
    const usable = OUTER_R - INNER_R - 20;
    const scoreRadius = INNER_R + 20 + (usable * d.score) / 100;
    return { ...d, startAngle, endAngle, midAngle, scoreRadius };
  });
};

/* -------------------------------------------------------------------------- */
/* Tiny presentational helpers                                                 */
/* -------------------------------------------------------------------------- */

const Sparkline = ({
  values,
  color,
  width = 88,
  height = 22,
}: {
  values: number[];
  color: string;
  width?: number;
  height?: number;
}) => {
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = Math.max(1, max - min);
  const stepX = width / Math.max(1, values.length - 1);
  const points = values
    .map((v, i) => {
      const x = i * stepX;
      const y = height - ((v - min) / range) * (height - 4) - 2;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      <polyline
        fill="none"
        stroke={color}
        strokeWidth={1.25}
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
      />
    </svg>
  );
};

const DeltaBadge = ({ delta }: { delta: number }) => {
  if (delta === 0) {
    return (
      <span
        style={{
          fontFamily: MONO,
          fontSize: 11,
          color: INK_FAINT,
          letterSpacing: "0.04em",
        }}
      >
        ±0
      </span>
    );
  }
  const positive = delta > 0;
  return (
    <span
      style={{
        fontFamily: MONO,
        fontSize: 11,
        color: positive ? OLIVE : TERRACOTTA,
        letterSpacing: "0.04em",
      }}
    >
      {positive ? "▲" : "▼"} {Math.abs(delta)}
    </span>
  );
};

const Dot = ({ color, size = 6 }: { color: string; size?: number }) => (
  <span
    style={{
      width: size,
      height: size,
      borderRadius: "50%",
      background: color,
      display: "inline-block",
    }}
  />
);

const SectionLabel = ({
  children,
  style,
}: {
  children: React.ReactNode;
  style?: React.CSSProperties;
}) => (
  <div
    style={{
      fontFamily: SANS,
      fontSize: 10.5,
      letterSpacing: "0.18em",
      textTransform: "uppercase",
      color: INK_FAINT,
      ...style,
    }}
  >
    {children}
  </div>
);

/* -------------------------------------------------------------------------- */
/* Left rail                                                                   */
/* -------------------------------------------------------------------------- */

const RailIcon = ({ d }: { d: string }) => (
  <svg
    width={18}
    height={18}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.4}
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d={d} />
  </svg>
);

const RAIL_ITEMS: { id: string; label: string; icon: string; active?: boolean }[] = [
  {
    id: "delphi",
    label: "Delphi",
    icon: "M12 3 L12 21 M3 12 L21 12 M5.6 5.6 L18.4 18.4 M5.6 18.4 L18.4 5.6",
    active: true,
  },
  {
    id: "inventory",
    label: "Inventory",
    icon: "M4 6 L20 6 M4 12 L20 12 M4 18 L14 18",
  },
  {
    id: "dsr",
    label: "Requests",
    icon: "M4 7 L20 7 L20 17 L4 17 Z M4 7 L12 13 L20 7",
  },
];

const LeftRail = () => (
  <aside
    style={{
      width: 44,
      flex: "0 0 44px",
      borderRight: `1px solid ${INK_HAIRLINE}`,
      background: "transparent",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      paddingTop: 28,
      paddingBottom: 24,
      gap: 2,
      position: "relative",
      zIndex: 1,
    }}
  >
    <div
      style={{
        fontFamily: SERIF,
        fontSize: 18,
        color: INK,
        lineHeight: 1,
        marginBottom: 28,
      }}
    >
      e
      <span
        style={{
          display: "inline-block",
          width: 3,
          height: 3,
          borderRadius: "50%",
          background: TERRACOTTA,
          marginLeft: 1,
          verticalAlign: "middle",
          transform: "translateY(-3px)",
        }}
      />
    </div>
    {RAIL_ITEMS.map((item) => (
      <button
        key={item.id}
        type="button"
        title={item.label}
        style={{
          width: 32,
          height: 32,
          border: "none",
          background: "transparent",
          color: item.active ? INK : INK_FAINT,
          borderRadius: 4,
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          position: "relative",
        }}
      >
        {item.active ? (
          <span
            style={{
              position: "absolute",
              left: -6,
              top: 8,
              bottom: 8,
              width: 1.5,
              background: TERRACOTTA,
            }}
          />
        ) : null}
        <RailIcon d={item.icon} />
      </button>
    ))}
    <div style={{ flex: 1 }} />
    <div
      style={{
        fontFamily: MONO,
        fontSize: 10,
        color: INK_FAINT,
        letterSpacing: "0.14em",
        writingMode: "vertical-rl",
        transform: "rotate(180deg)",
        marginBottom: 8,
      }}
    >
      KK
    </div>
  </aside>
);

/* -------------------------------------------------------------------------- */
/* Radial GPS                                                                  */
/* -------------------------------------------------------------------------- */

const labelAlignment = (angle: number) => {
  const norm = ((angle % 360) + 360) % 360;
  if (norm < 18 || norm > 342)
    return { textAlign: "center" as const, tx: "-50%", ty: "-100%" };
  if (norm > 162 && norm < 198)
    return { textAlign: "center" as const, tx: "-50%", ty: "0%" };
  if (norm >= 18 && norm <= 162)
    return { textAlign: "left" as const, tx: "0%", ty: "-50%" };
  return { textAlign: "right" as const, tx: "-100%", ty: "-50%" };
};

const GovernanceRadial = ({
  selected,
  onSelect,
}: {
  selected: DimensionId | null;
  onSelect: (id: DimensionId) => void;
}) => {
  const slices = useMemo(buildSlices, []);

  return (
    <div
      style={{
        position: "relative",
        width: SIZE,
        height: SIZE,
        margin: "0 auto",
      }}
    >
      <svg
        width={SIZE}
        height={SIZE}
        viewBox={`0 0 ${SIZE} ${SIZE}`}
        style={{ overflow: "visible", display: "block" }}
      >
        <defs>
          <radialGradient id="delphi-center" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor={PARCHMENT} />
            <stop offset="100%" stopColor={CORINTH_BG} />
          </radialGradient>
        </defs>

        {/* Faint guide rings */}
        {[0.33, 0.66, 1].map((t) => (
          <circle
            key={t}
            cx={CX}
            cy={CY}
            r={INNER_R + 20 + (OUTER_R - INNER_R - 20) * t}
            fill="none"
            stroke={INK_DOT}
            strokeWidth={1}
            strokeDasharray="1.5 4"
          />
        ))}

        {/* Radial dividers between slices */}
        {slices.map((s) => {
          const [x1, y1] = polar(CX, CY, INNER_R + 4, s.endAngle);
          const [x2, y2] = polar(CX, CY, OUTER_R + 6, s.endAngle);
          return (
            <line
              key={`div-${s.id}`}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke={INK_HAIRLINE}
              strokeWidth={1}
            />
          );
        })}

        {/* Score arcs (animated on selection) */}
        {slices.map((s) => {
          const start = s.startAngle + ARC_GAP_DEG;
          const end = s.endAngle - ARC_GAP_DEG;
          if (end <= start) return null;
          const isSelected = selected === s.id;
          const isDimmed = selected !== null && !isSelected;
          const color = statusColor(s.status);
          return (
            <motion.path
              key={`arc-${s.id}`}
              d={arcPath(CX, CY, s.scoreRadius, start, end)}
              fill="none"
              stroke={color}
              strokeLinecap="round"
              initial={false}
              animate={{
                strokeWidth: isSelected ? 7 : 4,
                opacity: isDimmed ? 0.35 : 1,
              }}
              transition={{ type: "spring", stiffness: 220, damping: 28 }}
            />
          );
        })}

        {/* Selection halo arc on outer perimeter */}
        {slices.map((s) => {
          const isSelected = selected === s.id;
          if (!isSelected) return null;
          const start = s.startAngle + ARC_GAP_DEG;
          const end = s.endAngle - ARC_GAP_DEG;
          return (
            <motion.path
              key={`halo-${s.id}`}
              d={arcPath(CX, CY, OUTER_R + 14, start, end)}
              fill="none"
              stroke={TERRACOTTA}
              strokeWidth={1.25}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            />
          );
        })}

        {/* Click targets — full wedges */}
        {slices.map((s) => (
          <path
            key={`hit-${s.id}`}
            d={wedgePath(
              CX,
              CY,
              INNER_R + 4,
              OUTER_R + 8,
              s.startAngle + 0.2,
              s.endAngle - 0.2,
            )}
            fill="transparent"
            style={{ cursor: "pointer" }}
            onClick={() => onSelect(s.id)}
          />
        ))}

        {/* Center disc */}
        <circle cx={CX} cy={CY} r={INNER_R} fill="url(#delphi-center)" />
        <circle
          cx={CX}
          cy={CY}
          r={INNER_R}
          fill="none"
          stroke={INK_HAIRLINE}
          strokeWidth={1}
        />
      </svg>

      {/* Center text */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          pointerEvents: "none",
        }}
      >
        <div
          style={{
            fontFamily: MONO,
            fontSize: 46,
            color: INK,
            lineHeight: 1,
            letterSpacing: "-0.02em",
          }}
        >
          {OVERALL_SCORE}
        </div>
        <div
          style={{
            fontFamily: SERIF,
            fontSize: 11,
            color: INK_MUTED,
            marginTop: 6,
            letterSpacing: "0.02em",
            textAlign: "center",
            maxWidth: 96,
            lineHeight: 1.3,
          }}
        >
          Overall Posture
        </div>
      </div>

      {/* Dimension labels */}
      {slices.map((s) => {
        const [lx, ly] = polar(CX, CY, LABEL_R, s.midAngle);
        const align = labelAlignment(s.midAngle);
        const isSelected = selected === s.id;
        return (
          <motion.button
            key={`label-${s.id}`}
            type="button"
            onClick={() => onSelect(s.id)}
            style={{
              position: "absolute",
              left: lx,
              top: ly,
              transform: `translate(${align.tx}, ${align.ty})`,
              textAlign: align.textAlign,
              minWidth: 96,
              background: "transparent",
              border: "none",
              padding: 0,
              cursor: "pointer",
              color: INK,
            }}
            initial={false}
            animate={{
              scale: isSelected ? 1.04 : 1,
              opacity: selected !== null && !isSelected ? 0.55 : 1,
            }}
            transition={{ type: "spring", stiffness: 260, damping: 26 }}
          >
            <div
              style={{
                fontFamily: SANS,
                fontSize: 10.5,
                letterSpacing: "0.14em",
                textTransform: "uppercase",
                color: INK_MUTED,
                marginBottom: 4,
              }}
            >
              {s.name}
            </div>
            <div
              style={{
                fontFamily: MONO,
                fontSize: 22,
                color: INK,
                lineHeight: 1,
              }}
            >
              {s.score}
            </div>
            <div
              style={{
                fontFamily: SANS,
                fontSize: 10,
                letterSpacing: "0.06em",
                color: INK_FAINT,
                marginTop: 4,
                display: "flex",
                alignItems: "center",
                gap: 6,
                justifyContent:
                  align.textAlign === "right"
                    ? "flex-end"
                    : align.textAlign === "center"
                      ? "center"
                      : "flex-start",
              }}
            >
              <Dot color={statusColor(s.status)} size={5} />
              <span>
                {statusLabel(s.status)} · {s.weight}%
              </span>
            </div>
          </motion.button>
        );
      })}
    </div>
  );
};

/* -------------------------------------------------------------------------- */
/* Ethyca AI                                                                   */
/* -------------------------------------------------------------------------- */

const DEFAULT_NARRATIVE =
  "Your governance posture is strong overall at 84. DSR and Policy Enforcement require attention. Select a dimension to inspect what changed, or ask a question below.";

const DEFAULT_PROMPTS = [
  "Why did DSR decline this week?",
  "Which policies are most violated?",
  "What changed in our data inventory?",
];

const promptsForDimension = (id: DimensionId): string[] => {
  if (id === "dsr")
    return [
      PROMPT_BY_DIMENSION.dsr,
      "Show me the slowest connectors.",
      "Which subjects are about to breach SLA?",
    ];
  if (id === "policy")
    return [
      PROMPT_BY_DIMENSION.policy,
      "Where is sensitive data living unexpectedly?",
      "What retention violations are largest?",
    ];
  if (id === "coverage")
    return [
      PROMPT_BY_DIMENSION.coverage,
      "List unmanaged data sources.",
      "Where is schema drift highest?",
    ];
  if (id === "classification")
    return [
      PROMPT_BY_DIMENSION.classification,
      "Show me low-confidence classifications.",
      "What new fields need a category?",
    ];
  if (id === "ai")
    return [
      PROMPT_BY_DIMENSION.ai,
      "Which AI systems drifted in risk?",
      "What vendor AI changes need review?",
    ];
  if (id === "consent")
    return [
      PROMPT_BY_DIMENSION.consent,
      "Where did consent rate drop?",
      "Which tags fired pre-consent?",
    ];
  return [
    PROMPT_BY_DIMENSION.assessment,
    "Show overdue impact assessments.",
    "Who owns assessment follow-ups?",
  ];
};

const EthycaAi = ({
  selected,
  promptValue,
  onPromptChange,
}: {
  selected: DimensionId | null;
  promptValue: string;
  onPromptChange: (v: string) => void;
}) => {
  const narrative = selected
    ? NARRATIVE_BY_DIMENSION[selected]
    : DEFAULT_NARRATIVE;
  const suggestions = selected ? promptsForDimension(selected) : DEFAULT_PROMPTS;

  return (
    <div style={{ marginTop: 56 }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          marginBottom: 18,
        }}
      >
        <span
          style={{
            width: 6,
            height: 6,
            borderRadius: "50%",
            background: TERRACOTTA,
            display: "inline-block",
          }}
        />
        <SectionLabel>Ethyca AI</SectionLabel>
      </div>

      <AnimatePresence mode="wait">
        <motion.p
          key={selected ?? "default"}
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -4 }}
          transition={{ duration: 0.22 }}
          style={{
            fontFamily: SERIF,
            fontSize: 28,
            lineHeight: 1.4,
            color: INK,
            letterSpacing: "-0.01em",
            margin: 0,
            maxWidth: 600,
            fontWeight: 400,
          }}
        >
          {narrative}
        </motion.p>
      </AnimatePresence>

      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: 8,
          marginTop: 18,
        }}
      >
        {suggestions.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => onPromptChange(s)}
            style={{
              fontFamily: SANS,
              fontSize: 12.5,
              color: INK_MUTED,
              background: "transparent",
              border: `1px solid ${INK_HAIRLINE}`,
              borderRadius: 999,
              padding: "6px 12px",
              cursor: "pointer",
              letterSpacing: "0.01em",
            }}
          >
            {s}
          </button>
        ))}
      </div>

      <div
        style={{
          marginTop: 18,
          display: "flex",
          alignItems: "center",
          gap: 12,
          padding: "12px 14px",
          background: "rgba(251, 250, 246, 0.7)",
          backdropFilter: "blur(8px)",
          WebkitBackdropFilter: "blur(8px)",
          border: `1px solid ${INK_HAIRLINE}`,
          borderRadius: 10,
          boxShadow: "0 1px 0 rgba(43, 45, 52, 0.02)",
        }}
      >
        <svg
          width={16}
          height={16}
          viewBox="0 0 24 24"
          fill="none"
          stroke={INK_FAINT}
          strokeWidth={1.5}
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M12 3 L12 21" />
          <path d="M3 12 L21 12" />
          <path d="M5.6 5.6 L18.4 18.4" />
          <path d="M5.6 18.4 L18.4 5.6" />
        </svg>
        <input
          value={promptValue}
          onChange={(e) => onPromptChange(e.target.value)}
          placeholder="Ask Delphi about your governance posture…"
          style={{
            flex: 1,
            background: "transparent",
            border: "none",
            outline: "none",
            fontFamily: SANS,
            fontSize: 14,
            color: INK,
            letterSpacing: "0.005em",
          }}
        />
        <button
          type="button"
          style={{
            fontFamily: SANS,
            fontSize: 11,
            letterSpacing: "0.12em",
            textTransform: "uppercase",
            color: INK,
            background: "transparent",
            border: `1px solid ${INK}`,
            borderRadius: 999,
            padding: "5px 12px",
            cursor: "pointer",
          }}
        >
          Ask
        </button>
      </div>
    </div>
  );
};

/* -------------------------------------------------------------------------- */
/* Recent movement (default right column)                                      */
/* -------------------------------------------------------------------------- */

const LedgerRow = ({
  dimension: d,
  isFirst,
  onSelect,
}: {
  dimension: Dimension;
  isFirst: boolean;
  onSelect: () => void;
}) => {
  const [hovered, setHovered] = useState(false);
  return (
    <motion.button
      type="button"
      onClick={onSelect}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      animate={{
        background: hovered
          ? "rgba(255, 255, 255, 0.85)"
          : "rgba(255, 255, 255, 0)",
        boxShadow: hovered
          ? "0 12px 28px -22px rgba(43, 45, 52, 0.28)"
          : "0 0 0 rgba(0,0,0,0)",
      }}
      transition={{ type: "spring", stiffness: 280, damping: 28 }}
      style={{
        position: "relative",
        textAlign: "left",
        display: "grid",
        gridTemplateColumns: "180px 76px 78px 1fr 96px",
        alignItems: "center",
        gap: 18,
        padding: "16px 20px",
        border: "none",
        borderTop: isFirst ? "none" : `1px solid ${INK_HAIRLINE}`,
        cursor: "pointer",
        color: INK,
        width: "100%",
        zIndex: hovered ? 2 : 1,
      }}
    >
      <div>
        <SectionLabel style={{ marginBottom: 4 }}>{d.name}</SectionLabel>
        <div
          style={{
            fontFamily: SANS,
            fontSize: 11.5,
            color: INK_FAINT,
            display: "flex",
            alignItems: "center",
            gap: 6,
          }}
        >
          <Dot color={statusColor(d.status)} size={5} />
          <span>{statusLabel(d.status)}</span>
        </div>
      </div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 3 }}>
        <span
          style={{
            fontFamily: MONO,
            fontSize: 24,
            color: INK,
            letterSpacing: "-0.01em",
            lineHeight: 1,
          }}
        >
          {d.score}
        </span>
        <span
          style={{
            fontFamily: MONO,
            fontSize: 11,
            color: INK_FAINT,
          }}
        >
          /100
        </span>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
        <SectionLabel>7d</SectionLabel>
        <DeltaBadge delta={d.delta7d} />
      </div>
      <div
        style={{
          fontFamily: SERIF,
          fontSize: 14,
          color: INK_MUTED,
          lineHeight: 1.4,
          letterSpacing: "-0.005em",
        }}
      >
        {d.driver}
      </div>
      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <Sparkline values={d.trend} color={statusColor(d.status)} />
      </div>
    </motion.button>
  );
};

const RecentMovement = ({
  onSelect,
}: {
  onSelect: (id: DimensionId) => void;
}) => {
  const rows = DIMENSIONS.filter((d) =>
    LICENSED_DIMENSIONS.includes(d.id),
  );

  return (
    <div>
      <header style={{ marginBottom: 20 }}>
        <h2
          style={{
            fontFamily: SERIF,
            fontSize: 28,
            color: INK,
            margin: 0,
            letterSpacing: "-0.01em",
            fontWeight: 400,
          }}
        >
          Recent movement
        </h2>
        <p
          style={{
            fontFamily: SANS,
            fontSize: 13,
            color: INK_MUTED,
            margin: "6px 0 0",
            lineHeight: 1.5,
            maxWidth: 480,
          }}
        >
          Signals Delphi detected across your licensed governance dimensions.
        </p>
      </header>

      <div
        style={{
          background: "rgba(255, 255, 255, 0.55)",
          backdropFilter: "blur(14px)",
          WebkitBackdropFilter: "blur(14px)",
          border: `1px solid ${INK_HAIRLINE}`,
          borderRadius: 12,
        }}
      >
        {rows.map((d, i) => (
          <LedgerRow
            key={d.id}
            dimension={d}
            isFirst={i === 0}
            onSelect={() => onSelect(d.id)}
          />
        ))}
      </div>
    </div>
  );
};

/* -------------------------------------------------------------------------- */
/* Decomposition (focused right column)                                        */
/* -------------------------------------------------------------------------- */

const priorityTone = (p: SignalCard["priority"]) => {
  if (p === "high") return TERRACOTTA;
  if (p === "med") return OLIVE;
  return INK_FAINT;
};

const SignalCardView = ({
  card,
  expanded,
  dimmed,
  onToggle,
}: {
  card: SignalCard;
  expanded: boolean;
  dimmed: boolean;
  onToggle: () => void;
}) => {
  const isSquare = card.shape === "square";
  return (
    <motion.div
      layout
      initial={false}
      animate={{ opacity: dimmed ? 0.5 : 1 }}
      transition={{ type: "spring", stiffness: 240, damping: 28 }}
      style={{
        gridColumn: card.shape === "wide" ? "span 2" : "span 1",
        background: "rgba(255, 255, 255, 0.7)",
        backdropFilter: "blur(12px)",
        WebkitBackdropFilter: "blur(12px)",
        border: `1px solid ${INK_HAIRLINE}`,
        borderRadius: 12,
        boxShadow: expanded
          ? "0 1px 0 rgba(43, 45, 52, 0.02), 0 18px 36px -22px rgba(43, 45, 52, 0.30)"
          : "0 1px 0 rgba(43, 45, 52, 0.02)",
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <motion.button
        layout
        type="button"
        onClick={onToggle}
        style={{
          width: "100%",
          textAlign: "left",
          background: "transparent",
          border: "none",
          padding: "16px 20px 4px",
          cursor: "pointer",
          color: INK,
          display: "flex",
          alignItems: "flex-start",
          gap: 16,
        }}
      >
        <div style={{ flex: 1, minWidth: 0 }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              marginBottom: 6,
            }}
          >
            <Dot color={priorityTone(card.priority)} size={6} />
            <SectionLabel>{card.title}</SectionLabel>
          </div>
          <div
            style={{
              fontFamily: SERIF,
              fontSize: 13.5,
              color: INK_MUTED,
              lineHeight: 1.4,
              letterSpacing: "-0.005em",
            }}
          >
            {card.summary}
          </div>
        </div>
        <div
          style={{
            display: "flex",
            alignItems: "baseline",
            gap: 4,
          }}
        >
          <span
            style={{
              fontFamily: MONO,
              fontSize: 28,
              color: INK,
              letterSpacing: "-0.01em",
              lineHeight: 1,
            }}
          >
            {card.count}
          </span>
          {card.unit ? (
            <span
              style={{
                fontFamily: MONO,
                fontSize: 11,
                color: INK_FAINT,
              }}
            >
              {card.unit}
            </span>
          ) : null}
        </div>
      </motion.button>

      {/* Default-state viz — always visible */}
      <div
        onClick={onToggle}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            onToggle();
          }
        }}
        style={{
          padding: isSquare ? "12px 20px 16px" : "10px 20px 16px",
          flex: 1,
          minHeight: isSquare ? 168 : undefined,
          display: "flex",
          alignItems: isSquare ? "center" : "flex-start",
          justifyContent: "center",
          cursor: "pointer",
        }}
      >
        <div style={{ width: "100%" }}>
          <CardViz id={card.id} />
        </div>
      </div>

      <AnimatePresence initial={false}>
        {expanded ? (
          <motion.div
            layout
            key="body"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ type: "spring", stiffness: 240, damping: 28 }}
            style={{ overflow: "hidden" }}
          >
            <div
              style={{
                padding: "16px 20px 20px",
                borderTop: `1px dashed ${INK_HAIRLINE}`,
              }}
            >
              <p
                style={{
                  fontFamily: SERIF,
                  fontSize: 14.5,
                  color: INK,
                  margin: "0 0 18px",
                  lineHeight: 1.55,
                  letterSpacing: "-0.005em",
                  maxWidth: 600,
                }}
              >
                {card.expanded}
              </p>
              <SectionLabel style={{ marginBottom: 8 }}>
                Top offenders
              </SectionLabel>
              <div style={{ marginBottom: 22 }}>
                {card.rows.slice(0, 3).map((row, i) => (
                  <div
                    key={row.label}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "10px 0",
                      borderTop:
                        i === 0 ? "none" : `1px solid ${INK_HAIRLINE}`,
                      fontFamily: SANS,
                      fontSize: 13,
                      color: INK,
                    }}
                  >
                    <span>{row.label}</span>
                    <span
                      style={{
                        fontFamily: MONO,
                        fontSize: 11.5,
                        color: INK_MUTED,
                        letterSpacing: "0.02em",
                      }}
                    >
                      {row.meta}
                    </span>
                  </div>
                ))}
              </div>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 16,
                }}
              >
                <button
                  type="button"
                  style={{
                    fontFamily: SANS,
                    fontSize: 11.5,
                    letterSpacing: "0.12em",
                    textTransform: "uppercase",
                    background: INK,
                    color: PARCHMENT,
                    border: "none",
                    borderRadius: 999,
                    padding: "9px 18px",
                    cursor: "pointer",
                  }}
                >
                  {card.primary}
                </button>
                <span
                  style={{
                    fontFamily: SANS,
                    fontSize: 11,
                    letterSpacing: "0.14em",
                    textTransform: "uppercase",
                    color: INK_FAINT,
                  }}
                >
                  {card.rows.length} total
                </span>
              </div>
            </div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </motion.div>
  );
};

const Decomposition = ({
  dimensionId,
  expandedId,
  onExpand,
  onClear,
}: {
  dimensionId: DimensionId;
  expandedId: string | null;
  onExpand: (id: string | null) => void;
  onClear: () => void;
}) => {
  const dimension = DIMENSIONS.find((d) => d.id === dimensionId);
  const cards = SIGNALS[dimensionId] ?? [];
  if (!dimension) return null;

  return (
    <div>
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          marginBottom: 20,
          gap: 24,
        }}
      >
        <div>
          <SectionLabel style={{ marginBottom: 8 }}>
            Decomposition · {dimension.name}
          </SectionLabel>
          <h2
            style={{
              fontFamily: SERIF,
              fontSize: 28,
              color: INK,
              margin: 0,
              letterSpacing: "-0.01em",
              fontWeight: 400,
            }}
          >
            What is moving the {dimension.name.toLowerCase()} score?
          </h2>
          <div
            style={{
              display: "flex",
              alignItems: "baseline",
              gap: 14,
              marginTop: 12,
            }}
          >
            <span
              style={{
                fontFamily: MONO,
                fontSize: 32,
                color: INK,
                letterSpacing: "-0.01em",
                lineHeight: 1,
              }}
            >
              {dimension.score}
            </span>
            <span
              style={{
                fontFamily: MONO,
                fontSize: 12,
                color: INK_FAINT,
              }}
            >
              /100
            </span>
            <DeltaBadge delta={dimension.delta7d} />
            <span
              style={{
                fontFamily: SANS,
                fontSize: 11,
                letterSpacing: "0.14em",
                textTransform: "uppercase",
                color: INK_FAINT,
              }}
            >
              7-day
            </span>
          </div>
        </div>
        <button
          type="button"
          onClick={onClear}
          style={{
            fontFamily: SANS,
            fontSize: 11,
            letterSpacing: "0.14em",
            textTransform: "uppercase",
            color: INK_MUTED,
            background: "transparent",
            border: `1px solid ${INK_HAIRLINE}`,
            borderRadius: 999,
            padding: "6px 12px",
            cursor: "pointer",
          }}
        >
          ← Recent movement
        </button>
      </div>

      <motion.div
        layout
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gridAutoFlow: "dense",
          gap: 12,
          alignItems: "stretch",
        }}
      >
        <AnimatePresence initial={false}>
          {cards.map((card) => (
            <SignalCardView
              key={card.id}
              card={card}
              expanded={expandedId === card.id}
              dimmed={expandedId !== null && expandedId !== card.id}
              onToggle={() =>
                onExpand(expandedId === card.id ? null : card.id)
              }
            />
          ))}
        </AnimatePresence>
      </motion.div>

      {cards.length === 0 ? (
        <div
          style={{
            fontFamily: SERIF,
            fontSize: 16,
            color: INK_MUTED,
            padding: 24,
            border: `1px dashed ${INK_HAIRLINE}`,
            borderRadius: 12,
          }}
        >
          No decomposition cards configured for this dimension.
        </div>
      ) : null}
    </div>
  );
};

/* -------------------------------------------------------------------------- */
/* Page                                                                        */
/* -------------------------------------------------------------------------- */

const DelphiCommandCenter = () => {
  const [selectedDimension, setSelectedDimension] = useState<DimensionId | null>(
    null,
  );
  const [expandedSignalCard, setExpandedSignalCard] = useState<string | null>(
    null,
  );
  const [promptValue, setPromptValue] = useState("");

  const selectDimension = (id: DimensionId) => {
    if (selectedDimension === id) {
      setSelectedDimension(null);
      setExpandedSignalCard(null);
      setPromptValue("");
      return;
    }
    setSelectedDimension(id);
    setExpandedSignalCard(null);
    setPromptValue(PROMPT_BY_DIMENSION[id]);
  };

  const clearSelection = () => {
    setSelectedDimension(null);
    setExpandedSignalCard(null);
    setPromptValue("");
  };

  return (
    <div
      style={{
        width: "100%",
        minHeight: "100vh",
        background: CORINTH_BG,
        color: INK,
        fontFamily: SANS,
        display: "flex",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Soft floating shade — VERY subtle, opaque #CDD2D3 blurred */}
      <div
        aria-hidden
        style={{
          position: "fixed",
          top: "-20%",
          right: "-15%",
          width: 1200,
          height: 1200,
          borderRadius: "50%",
          background: SHADE,
          filter: "blur(220px)",
          opacity: 0.55,
          pointerEvents: "none",
          zIndex: 0,
        }}
      />
      <div
        aria-hidden
        style={{
          position: "fixed",
          bottom: "-25%",
          left: "-12%",
          width: 1000,
          height: 1000,
          borderRadius: "50%",
          background: SHADE,
          filter: "blur(220px)",
          opacity: 0.4,
          pointerEvents: "none",
          zIndex: 0,
        }}
      />

      <LeftRail />

      <main
        style={{
          flex: 1,
          minWidth: 0,
          width: "100%",
          maxWidth: 1400,
          marginLeft: "auto",
          marginRight: "auto",
          display: "grid",
          gridTemplateColumns: "minmax(520px, 45fr) minmax(560px, 55fr)",
          gap: 0,
          position: "relative",
          zIndex: 1,
        }}
      >
        {/* LEFT COLUMN — intelligence core */}
        <section
          style={{
            padding: "40px 48px 56px 56px",
            borderRight: `1px solid ${INK_HAIRLINE}`,
            display: "flex",
            flexDirection: "column",
            minWidth: 0,
          }}
        >
          <header
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: 28,
            }}
          >
            <div
              style={{
                fontFamily: SERIF,
                fontSize: 22,
                letterSpacing: "0.01em",
                color: INK,
              }}
            >
              ethyca
              <span
                style={{
                  display: "inline-block",
                  width: 4,
                  height: 4,
                  borderRadius: "50%",
                  background: TERRACOTTA,
                  marginLeft: 4,
                  verticalAlign: "middle",
                  transform: "translateY(-3px)",
                }}
              />
            </div>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                color: INK_FAINT,
              }}
            >
              <SectionLabel>Delphi · Command</SectionLabel>
              <span style={{ fontFamily: MONO, fontSize: 11 }}>
                {new Date().toLocaleDateString("en-US", {
                  weekday: "short",
                  month: "short",
                  day: "numeric",
                })}
              </span>
            </div>
          </header>

          <div style={{ marginBottom: 12 }}>
            <SectionLabel style={{ marginBottom: 8 }}>
              Governance Posture Score
            </SectionLabel>
            <h1
              style={{
                fontFamily: SERIF,
                fontSize: 34,
                color: INK,
                margin: 0,
                letterSpacing: "-0.01em",
                fontWeight: 400,
                lineHeight: 1.15,
              }}
            >
              Good morning, Karolis.
            </h1>
          </div>

          <div style={{ marginTop: 18, marginBottom: 4 }}>
            <GovernanceRadial
              selected={selectedDimension}
              onSelect={selectDimension}
            />
          </div>

          <EthycaAi
            selected={selectedDimension}
            promptValue={promptValue}
            onPromptChange={setPromptValue}
          />
        </section>

        {/* RIGHT COLUMN — operational context */}
        <section
          style={{
            padding: "40px 56px 56px 48px",
            minWidth: 0,
            position: "relative",
          }}
        >
          <AnimatePresence mode="wait">
            {selectedDimension ? (
              <motion.div
                key={`focus-${selectedDimension}`}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                transition={{ duration: 0.22 }}
              >
                <Decomposition
                  dimensionId={selectedDimension}
                  expandedId={expandedSignalCard}
                  onExpand={setExpandedSignalCard}
                  onClear={clearSelection}
                />
              </motion.div>
            ) : (
              <motion.div
                key="recent"
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                transition={{ duration: 0.22 }}
              >
                <RecentMovement onSelect={selectDimension} />
              </motion.div>
            )}
          </AnimatePresence>
        </section>
      </main>
    </div>
  );
};

export default DelphiCommandCenter;
