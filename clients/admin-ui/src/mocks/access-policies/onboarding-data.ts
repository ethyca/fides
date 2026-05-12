/** Human-readable labels for each industry key. */
export const INDUSTRY_LABELS: Record<string, string> = {
  fintech: "Fintech",
  healthcare: "Healthcare",
  retail: "Retail & E-Commerce",
  saas: "SaaS / Technology",
  insurance: "Insurance",
  government: "Government",
};

/** Industry-specific data uses mapped to fideslang taxonomy keys. */
export const INDUSTRY_DATA_USES: Record<string, string[]> = {
  fintech: [
    "essential.fraud_detection",
    "analytics.reporting",
    "essential.service.payment_processing",
    "essential.legal_obligation",
    "marketing.advertising.profiling",
    "personalize.content",
    "essential.service.operations.support",
  ],
  healthcare: [
    "essential.service.operations",
    "analytics.reporting",
    "essential.service.payment_processing",
    "essential.legal_obligation",
    "personalize.content",
    "essential.service.operations.support",
    "third_party_sharing",
  ],
  retail: [
    "personalize.content",
    "analytics.reporting",
    "marketing.advertising.profiling",
    "marketing.communications.email",
    "essential.fraud_detection",
    "essential.service.operations.support",
    "functional.service.improve",
  ],
  saas: [
    "analytics.reporting",
    "functional.service.improve",
    "personalize.content",
    "marketing.advertising.profiling",
    "essential.service.operations.support",
    "essential.fraud_detection",
    "train_ai_system",
  ],
  insurance: [
    "essential.fraud_detection",
    "analytics.reporting",
    "essential.service.payment_processing",
    "essential.legal_obligation",
    "personalize.content",
    "essential.service.operations.support",
    "third_party_sharing",
  ],
  government: [
    "essential.service.operations",
    "essential.service.security",
    "essential.legal_obligation",
    "employment",
    "analytics.reporting",
    "essential.service.operations.support",
    "third_party_sharing",
  ],
};

/** Geography-specific data uses appended to the industry set. */
export const GEO_DATA_USES: Record<string, string[]> = {
  eea: ["functional.storage.privacy_preferences"],
  us: ["marketing.advertising.third_party.targeted"],
};
