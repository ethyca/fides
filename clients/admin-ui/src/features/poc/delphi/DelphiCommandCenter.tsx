import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useMemo, useRef, useState } from "react";

import { CardViz } from "./DelphiCardViz";
import DelphiHeader, { DELPHI_HEADER_HEIGHT } from "./DelphiHeader";
import DelphiSideNav, { DELPHI_RAIL_WIDTH } from "./DelphiSideNav";

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
const INK_HAIRLINE = "rgba(43, 45, 52, 0.16)";
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
    "Coverage holds at 92 — the dimension's strongest position in eleven weeks. Six new data sources entered inventory in the last seven days, four already classified and assigned to owners.\n\nTwo unmanaged S3 buckets surfaced via network logs and need owners. Schema drift is the lighter concern: eighteen new fields appeared in monitored schemas without classification, mostly in growth product tables. Fulfillment connector reach is steady at 91% of inventory.",
  classification:
    "Classification slipped two points to 71. Forty-two fields lack a category across the data map, the bulk concentrated in marketing and product analytics tables. Eighteen low-confidence tags are queued for manual review.\n\nThe bigger signal is structural: nine downstream tables now derive from new upstream sources, and lineage changes mean classification needs revalidation on dim_users, fct_orders, and seven others. Eleven sensitive fields appeared in datasets the data map does not designate sensitive — these read as policy violations under enforcement, but the source-of-truth fix is here.",
  consent:
    "Consent is at 64 and slipping. Acceptance rate fell across the EU and UK over the last thirty days, with the largest drop in Germany at minus seven points — aligned with a banner copy change shipped May 1. Three pre-consent tag fires were detected on /checkout, /blog, and /pricing.\n\nFour jurisdictions are missing or running stale consent surfaces: Brazil has no banner deployed, Australia is on a notice version pulled in March, and India and Mexico have partial coverage. Fourteen consent records fail integrity checks today — above the ten-per-day baseline, with timestamp drift accounting for most of the gap.",
  dsr:
    "DSR fell four points to 76. Twenty-three requests are within forty-eight hours of SLA breach, most originating from the Acme connector queue where identity verification has stalled. Five fulfillment steps failed in the last forty-eight hours, concentrated on Postgres deletions and HubSpot lookups.\n\nEight stuck requests are awaiting verification or downstream response — the Salesforce connector has not acknowledged in thirty-six hours. Three subjects have escalated after a prior response was rejected, all three relating to the same retention policy on analytics events. The verification queue is fourteen deep with average wait running nineteen hours, above the twelve-hour target.",
  policy:
    "Policy Enforcement is at 58 and trending down. Seven datasets contain records that have exceeded their declared retention; the largest is analytics_events with 1.2 million rows past policy. Eleven sensitive fields appeared in datasets the data map does not designate sensitive.\n\nFive third-party tags fired before consent on at least one production page — two are ad-network pixels, one is a session tool. Two AI deployments triggered policy violations: support-bot v3 missing impact assessment, fraud-classifier with a prohibited input category. None of these are passive failures; each maps to an owner and a remediation step.",
  ai:
    "AI Readiness is at 81 with three new AI systems detected this week — two internal services and one third-party vendor capability. Four existing systems drifted upward in risk tier since their last review, including two now classified high-risk: fraud-classifier and pricing-optimizer.\n\nOne training dataset contains records flagged sensitive without an explicit lawful basis. Two vendors changed AI usage or training-data terms within the last fourteen days — Zendesk and Notion both warrant a legal review. Six EU AI Act controls have not been refreshed in ninety days, including the Article 10 data governance and Article 13 transparency mappings.",
  assessment:
    "Assessment Coverage is at 87. Eight assessments are awaiting reviewer pickup, with the oldest at six days — past the five-day SLA. Five assessments are past their declared reassessment date, the oldest being Marketing AI at 124 days.\n\nTwo systems classified high-risk are operating without a current DPIA: fraud-classifier and lead-gen scoring. Both require remediation before the next audit cycle. Five newly detected AI systems are queued for assessment intake — three vendor capabilities, two internal services. Six reassessments fall within the next thirty days; two are inside the seven-day attention window.",
};

const DEFAULT_NARRATIVE_TEXT =
  "Your governance posture sits at 84 — strong overall, but three dimensions are trending in the wrong direction. DSR fell four points to 76, Consent dropped one to 64, and Policy Enforcement remains the lowest-scoring dimension at 58.\n\nThe DSR slip is the most actionable: twenty-three requests are within forty-eight hours of statutory breach, concentrated in the Acme connector queue where verification has stalled. Policy Enforcement and Consent are slower drifts — retention violations on analytics_events accumulated this week, and three pre-consent tag fires were detected on production pages. Coverage and AI Readiness held their ground, with six new data sources and three new AI systems entering inventory cleanly.";

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

const DEFAULT_NARRATIVE = DEFAULT_NARRATIVE_TEXT;

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

const EthycaNarrative = ({
  selected,
}: {
  selected: DimensionId | null;
}) => {
  const narrative = selected
    ? NARRATIVE_BY_DIMENSION[selected]
    : DEFAULT_NARRATIVE;
  const paragraphs = narrative.split("\n\n");
  return (
    <div style={{ marginTop: 32 }}>
      <AnimatePresence mode="wait">
        <motion.div
          key={selected ?? "default"}
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -4 }}
          transition={{ duration: 0.22 }}
          style={{ maxWidth: 640 }}
        >
          {paragraphs.map((p, i) => (
            <p
              key={i}
              style={{
                fontFamily: SERIF,
                fontSize: 24,
                lineHeight: 1.45,
                color: INK,
                letterSpacing: "-0.01em",
                margin: 0,
                marginTop: i === 0 ? 0 : "1em",
                fontWeight: 400,
              }}
            >
              {p}
            </p>
          ))}
        </motion.div>
      </AnimatePresence>
    </div>
  );
};

const AskDelphiBar = ({
  selected,
  promptValue,
  onPromptChange,
}: {
  selected: DimensionId | null;
  promptValue: string;
  onPromptChange: (v: string) => void;
}) => {
  const suggestions = selected ? promptsForDimension(selected) : DEFAULT_PROMPTS;
  return (
    <div
      style={{
        position: "fixed",
        bottom: 0,
        left: DELPHI_RAIL_WIDTH,
        right: 0,
        zIndex: 30,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          maxWidth: 1400,
          margin: "0 auto",
          display: "grid",
          gridTemplateColumns: "minmax(520px, 45fr) minmax(560px, 55fr)",
        }}
      >
        <div
          style={{
            padding: "20px 48px 28px 56px",
            display: "flex",
            flexDirection: "column",
            gap: 12,
            pointerEvents: "auto",
          }}
        >
          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: 8,
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
                  background: "rgba(255, 255, 255, 0.55)",
                  backdropFilter: "blur(8px)",
                  WebkitBackdropFilter: "blur(8px)",
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
              display: "flex",
              alignItems: "center",
              gap: 12,
              padding: "12px 14px",
              background: "rgba(255, 255, 255, 0.55)",
              backdropFilter: "blur(14px)",
              WebkitBackdropFilter: "blur(14px)",
              border: `1px solid ${INK_HAIRLINE}`,
              borderRadius: 0,
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
        <div />
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
          borderRadius: 0,
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

const CornerTicks = ({ visible }: { visible: boolean }) => {
  const size = 8;
  const w = 1;
  const c = INK_HAIRLINE;
  const corners: React.CSSProperties[] = [
    { top: 0, left: 0, borderTop: `${w}px solid ${c}`, borderLeft: `${w}px solid ${c}` },
    { top: 0, right: 0, borderTop: `${w}px solid ${c}`, borderRight: `${w}px solid ${c}` },
    { bottom: 0, left: 0, borderBottom: `${w}px solid ${c}`, borderLeft: `${w}px solid ${c}` },
    { bottom: 0, right: 0, borderBottom: `${w}px solid ${c}`, borderRight: `${w}px solid ${c}` },
  ];
  return (
    <motion.div
      initial={false}
      animate={{ opacity: visible ? 1 : 0 }}
      transition={{ duration: 0.18 }}
      style={{ position: "absolute", inset: 0, pointerEvents: "none" }}
    >
      {corners.map((style, i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            width: size,
            height: size,
            ...style,
          }}
        />
      ))}
    </motion.div>
  );
};

const CardCollapsedBody = ({ card }: { card: SignalCard }) => {
  const isSquare = card.shape === "square";
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
      }}
    >
      <div
        style={{
          padding: "14px 16px 4px",
          display: "flex",
          alignItems: "flex-start",
          gap: 14,
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
        <div style={{ display: "flex", alignItems: "baseline", gap: 4 }}>
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
            <span style={{ fontFamily: MONO, fontSize: 11, color: INK_FAINT }}>
              {card.unit}
            </span>
          ) : null}
        </div>
      </div>
      <div
        style={{
          padding: isSquare ? "10px 16px 14px" : "8px 16px 14px",
          flex: 1,
          minHeight: isSquare ? 156 : undefined,
          display: "flex",
          alignItems: isSquare ? "center" : "flex-start",
          justifyContent: "center",
        }}
      >
        <div style={{ width: "100%" }}>
          <CardViz id={card.id} />
        </div>
      </div>
    </div>
  );
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
  onToggle: (rect?: DOMRect) => void;
}) => {
  const [hovered, setHovered] = useState(false);
  const cardRef = useRef<HTMLDivElement>(null);
  const handleActivate = () => {
    onToggle(cardRef.current?.getBoundingClientRect());
  };
  return (
    <div
      style={{
        gridColumn: card.shape === "wide" ? "span 2" : "span 1",
        position: "relative",
      }}
    >
      {/* Always-present invisible spacer maintains the slot's dimensions */}
      <div style={{ visibility: "hidden" }} aria-hidden>
        <CardCollapsedBody card={card} />
      </div>

      {/* The actual card; unmounts when expanded so the layoutId moves to the modal */}
      <AnimatePresence initial={false}>
        {!expanded ? (
          <motion.div
            key="card"
            ref={cardRef}
            layoutId={`signal-card-${card.id}`}
            initial={{ opacity: 1 }}
            animate={{ opacity: dimmed ? 0.5 : 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.18 }}
            onMouseEnter={() => setHovered(true)}
            onMouseLeave={() => setHovered(false)}
            onClick={handleActivate}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                handleActivate();
              }
            }}
            role="button"
            tabIndex={0}
            style={{
              position: "absolute",
              inset: 0,
              borderRadius: 0,
              cursor: "pointer",
              color: INK,
              background: "rgba(255, 255, 255, 0.20)",
              backdropFilter: "blur(8px)",
              WebkitBackdropFilter: "blur(8px)",
            }}
          >
            {/* Frosted glass surface that fades in on hover */}
            <motion.div
              initial={false}
              animate={{ opacity: hovered ? 1 : 0 }}
              transition={{ duration: 0.18 }}
              style={{
                position: "absolute",
                inset: 0,
                borderRadius: 0,
                background: "rgba(255, 255, 255, 0.55)",
                backdropFilter: "blur(12px)",
                WebkitBackdropFilter: "blur(12px)",
                border: `1px solid ${INK_HAIRLINE}`,
                pointerEvents: "none",
              }}
            />
            {/* Corner ticks at rest */}
            <CornerTicks visible={!hovered} />
            <div style={{ position: "relative", zIndex: 1 }}>
              <CardCollapsedBody card={card} />
            </div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </div>
  );
};

const SignalCardModal = ({
  card,
  anchor,
  onClose,
}: {
  card: SignalCard;
  anchor: DOMRect | null;
  onClose: () => void;
}) => {
  // Close on Escape
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  // Position the modal at (or near) the card's anchor, then clamp to viewport.
  // Width grows from the anchor's left edge; height clamped to viewport.
  const pos = useMemo(() => {
    const PAD = 16;
    const TOP_GUARD = 70; // clear of fixed header
    const MIN_WIDTH = 480;
    const TARGET_WIDTH = 640;
    if (typeof window === "undefined" || !anchor) {
      return {
        top: "10vh",
        left: "calc(50vw - 320px)",
        width: TARGET_WIDTH,
        maxHeight: "70vh",
      };
    }
    const desiredWidth = Math.min(
      TARGET_WIDTH,
      Math.max(MIN_WIDTH, anchor.width * 1.6),
      window.innerWidth - PAD * 2,
    );
    const maxHeight = Math.min(window.innerHeight - TOP_GUARD - PAD, 640);
    const left = Math.max(
      PAD,
      Math.min(anchor.left, window.innerWidth - desiredWidth - PAD),
    );
    const top = Math.max(
      TOP_GUARD,
      Math.min(anchor.top, window.innerHeight - maxHeight - PAD),
    );
    return { top, left, width: desiredWidth, maxHeight };
  }, [anchor]);

  return (
    <>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.2 }}
        onClick={onClose}
        style={{
          position: "fixed",
          inset: 0,
          background: "rgba(43, 45, 52, 0.18)",
          backdropFilter: "blur(3px)",
          WebkitBackdropFilter: "blur(3px)",
          zIndex: 100,
        }}
      />
      <motion.div
        layoutId={`signal-card-${card.id}`}
        transition={{ type: "spring", stiffness: 260, damping: 30 }}
        style={{
          position: "fixed",
          top: pos.top,
          left: pos.left,
          width: pos.width,
          maxHeight: pos.maxHeight,
          background: "rgba(255, 255, 255, 0.38)",
          backdropFilter: "blur(24px)",
          WebkitBackdropFilter: "blur(24px)",
          borderRadius: 0,
          border: `1px solid ${INK_HAIRLINE}`,
          boxShadow:
            "0 1px 0 rgba(43, 45, 52, 0.02), 0 32px 70px -16px rgba(43, 45, 52, 0.42)",
          zIndex: 101,
          overflow: "auto",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <CardCollapsedBody card={card} />
        <motion.div
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0 }}
          transition={{ delay: 0.1, duration: 0.22 }}
          style={{
            padding: "0 20px 24px",
            borderTop: `1px dashed ${INK_HAIRLINE}`,
            marginTop: 4,
            paddingTop: 18,
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
          <SectionLabel style={{ marginBottom: 8 }}>Top offenders</SectionLabel>
          <div style={{ marginBottom: 22 }}>
            {card.rows.slice(0, 3).map((row, i) => (
              <div
                key={row.label}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "10px 0",
                  borderTop: i === 0 ? "none" : `1px solid ${INK_HAIRLINE}`,
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
            style={{ display: "flex", alignItems: "center", gap: 16 }}
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
        </motion.div>
      </motion.div>
    </>
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
  const [anchor, setAnchor] = useState<DOMRect | null>(null);

  const handleToggle = (id: string) => (rect?: DOMRect) => {
    const isOpening = expandedId !== id;
    setAnchor(isOpening && rect ? rect : null);
    onExpand(isOpening ? id : null);
  };
  const handleClose = () => {
    setAnchor(null);
    onExpand(null);
  };

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
          <div
            style={{
              display: "flex",
              alignItems: "baseline",
              gap: 14,
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
          gap: 24,
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
              onToggle={handleToggle(card.id)}
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
            borderRadius: 0,
          }}
        >
          No decomposition cards configured for this dimension.
        </div>
      ) : null}

      <AnimatePresence>
        {expandedId
          ? (() => {
              const card = cards.find((c) => c.id === expandedId);
              return card ? (
                <SignalCardModal
                  key={card.id}
                  card={card}
                  anchor={anchor}
                  onClose={handleClose}
                />
              ) : null;
            })()
          : null}
      </AnimatePresence>
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
        position: "relative",
        overflow: "hidden",
        paddingLeft: DELPHI_RAIL_WIDTH,
        boxSizing: "border-box",
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

      <DelphiHeader />
      <DelphiSideNav />

      <main
        style={{
          width: "100%",
          maxWidth: 1400,
          marginLeft: "auto",
          marginRight: "auto",
          paddingTop: DELPHI_HEADER_HEIGHT,
          paddingBottom: 160,
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
            display: "flex",
            flexDirection: "column",
            minWidth: 0,
          }}
        >
          <div style={{ marginTop: 4, marginBottom: 4 }}>
            <GovernanceRadial
              selected={selectedDimension}
              onSelect={selectDimension}
            />
          </div>

          <EthycaNarrative selected={selectedDimension} />
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

      <AskDelphiBar
        selected={selectedDimension}
        promptValue={promptValue}
        onPromptChange={setPromptValue}
      />
    </div>
  );
};

export default DelphiCommandCenter;
