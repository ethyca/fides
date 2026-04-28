import { AccessPolicy } from "~/features/access-policies/access-policies.slice";

/**
 * Returns a set of policies that the "generate" endpoint would produce.
 * Each call returns fresh objects with unique IDs so they can be pushed
 * into the mutable policies array multiple times without conflicts.
 */
export const generatedPoliciesForIndustry = (): AccessPolicy[] => {
  const now = new Date().toISOString();
  const id = () =>
    `gen-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;

  return [
    {
      id: id(),
      name: "Marketing Data — Consent Required",
      description:
        "Deny access to marketing and profiling data unless the user has opted in to marketing consent.",
      control: "eea_uk_gdpr",
      is_recommendation: true,
      yaml: [
        "name: Marketing Data — Consent Required",
        "description: Deny marketing/profiling data access without opt-in consent",
        "enabled: true",
        "priority: 100",
        "controls:",
        "  - eea_uk_gdpr",
        "  - us_glba_ccpa",
        "decision: DENY",
        "match:",
        "  data_use:",
        "    any:",
        "      - marketing.advertising.profiling",
        "      - marketing.communications.email",
        "      - marketing.advertising.third_party.targeted",
        "unless:",
        "  - type: consent",
        "    privacy_notice_key: marketing_opt_in",
        "    requirement: opt_in",
        "action:",
        "  message: Access denied — marketing consent not obtained",
      ].join("\n"),
      created_at: now,
      updated_at: now,
    },
    {
      id: id(),
      name: "Fraud Detection — Legitimate Interest",
      description:
        "Allow access to fraud detection data under legitimate interest without additional consent.",
      control: "global",
      is_recommendation: true,
      yaml: [
        "name: Fraud Detection — Legitimate Interest",
        "description: Allow fraud detection data access under legitimate interest",
        "enabled: true",
        "priority: 200",
        "controls:",
        "  - global",
        "decision: ALLOW",
        "match:",
        "  data_use:",
        "    any:",
        "      - essential.fraud_detection",
        "      - essential.service.security",
      ].join("\n"),
      created_at: now,
      updated_at: now,
    },
    {
      id: id(),
      name: "Analytics — EEA Geo Restriction",
      description:
        "Deny analytics data processing for EEA residents unless consent is provided.",
      control: "eea_uk_gdpr",
      is_recommendation: true,
      yaml: [
        "name: Analytics — EEA Geo Restriction",
        "description: Deny analytics processing for EEA residents without consent",
        "enabled: true",
        "priority: 300",
        "controls:",
        "  - eea_uk_gdpr",
        "decision: DENY",
        "match:",
        "  data_use:",
        "    any:",
        "      - analytics.reporting",
        "unless:",
        "  - type: consent",
        "    privacy_notice_key: analytics_consent",
        "    requirement: opt_in",
        "  - type: geo_location",
        "    field: data_subject.geo_location",
        "    operator: not_in",
        "    values:",
        "      - eea",
        "action:",
        "  message: Analytics consent required for EEA data subjects",
      ].join("\n"),
      created_at: now,
      updated_at: now,
    },
    {
      id: id(),
      name: "Payment Processing — Contract Basis",
      description:
        "Allow payment processing data access as necessary for contract fulfillment.",
      control: "global",
      yaml: [
        "name: Payment Processing — Contract Basis",
        "description: Allow payment processing under contractual necessity",
        "enabled: true",
        "priority: 400",
        "controls:",
        "  - global",
        "decision: ALLOW",
        "match:",
        "  data_use:",
        "    any:",
        "      - essential.service.payment_processing",
      ].join("\n"),
      created_at: now,
      updated_at: now,
    },
  ];
};
