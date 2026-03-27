import { PolicyCategory } from "./types";

export const MOCK_POLICY_CATEGORIES: PolicyCategory[] = [
  {
    id: "customer_pii_access",
    title: "Customer PII access",
    drivenBy: "GDPR Articles 5, 6 — Purpose limitation and lawful basis",
    policies: [
      {
        id: "kyc_data_role_restriction",
        title: "KYC data role restriction",
        description:
          "Limits access to Know Your Customer identity documents and verification records to compliance and onboarding teams only.",
        isRecommendation: true,
        isNew: true,
        isEnabled: true,
        violationCount: 8,
        dataUseTags: ["KYC", "Identity"],
        lastUpdated: "2m ago",
      },
      {
        id: "contact_data_purpose_binding",
        title: "Contact data purpose binding",
        description:
          "Restricts access to customer email addresses and phone numbers to service delivery contexts, blocking use for marketing without consent.",
        isRecommendation: false,
        isEnabled: true,
        violationCount: 0,
        dataUseTags: ["Support", "Marketing"],
        lastUpdated: "14m ago",
      },
      {
        id: "consent_gated_profile_access",
        title: "Consent-gated profile access",
        description:
          "Blocks downstream queries on customer profiles where consent preferences have not been recorded or have expired beyond the renewal window.",
        isRecommendation: true,
        isNew: true,
        isEnabled: false,
        violationCount: 5,
        dataUseTags: ["Marketing", "Analytics"],
        lastUpdated: "4h ago",
      },
      {
        id: "customer_data_retention_access",
        title: "Customer data retention access",
        description:
          "Prevents read or export access to customer records that have exceeded the configured 24-month retention window pending deletion review.",
        isRecommendation: false,
        isEnabled: true,
        violationCount: 0,
        dataUseTags: ["Compliance"],
        lastUpdated: "1d ago",
      },
      {
        id: "third_party_data_sharing",
        title: "Third-party data sharing access",
        description:
          "Requires explicit data-sharing agreements before granting partner or vendor systems read access to customer account and transaction summaries.",
        isRecommendation: true,
        isNew: true,
        isEnabled: false,
        violationCount: 3,
        dataUseTags: ["Vendors", "Open Banking"],
        lastUpdated: "8h ago",
      },
    ],
  },
  {
    id: "financial_transaction_access",
    title: "Financial & transaction data access",
    drivenBy: "PSD2, PCI-DSS — Payment data security and strong authentication",
    policies: [
      {
        id: "cardholder_data_access",
        title: "Cardholder data access",
        description:
          "Restricts access to detokenized card numbers and CVVs to PCI-certified service accounts within the payment processing environment.",
        isRecommendation: true,
        isNew: true,
        isEnabled: true,
        violationCount: 1,
        dataUseTags: ["Payments", "PCI"],
        lastUpdated: "1h ago",
      },
      {
        id: "transaction_log_access",
        title: "Transaction log access",
        description:
          "Requires an approval workflow before granting access to raw payment logs for transactions exceeding $50k in aggregate value.",
        isRecommendation: false,
        isEnabled: true,
        violationCount: 0,
        dataUseTags: ["Payments", "Audit"],
        lastUpdated: "Just now",
      },
      {
        id: "bulk_financial_export",
        title: "Bulk financial export restriction",
        description:
          "Blocks queries attempting to export more than 10,000 records from account balance and transaction history tables without manager approval.",
        isRecommendation: true,
        isEnabled: true,
        violationCount: 3,
        dataUseTags: ["Fraud", "Compliance"],
        lastUpdated: "2d ago",
      },
    ],
  },
  {
    id: "aml_fraud_data_access",
    title: "AML & fraud investigation access",
    drivenBy:
      "BSA/AML, EU AMLD6 — Anti-money laundering and suspicious activity reporting",
    policies: [
      {
        id: "sar_data_access",
        title: "SAR filing data access",
        description:
          "Limits access to Suspicious Activity Report records and supporting evidence to designated BSA officers and compliance investigators.",
        isRecommendation: false,
        isEnabled: true,
        violationCount: 14,
        dataUseTags: ["AML", "Compliance"],
        lastUpdated: "3h ago",
      },
      {
        id: "fraud_model_training_access",
        title: "Fraud model training data access",
        description:
          "Controls which teams can access labeled fraud datasets used for model training, restricting to data science roles with approved use cases.",
        isRecommendation: false,
        isEnabled: true,
        violationCount: 2,
        dataUseTags: ["Fraud", "ML"],
        lastUpdated: "6d ago",
      },
      {
        id: "watchlist_screening_access",
        title: "Watchlist screening access",
        description:
          "Restricts access to sanctions and PEP screening results to compliance and legal teams, preventing exposure to general customer service roles.",
        isRecommendation: true,
        isNew: true,
        isEnabled: false,
        violationCount: 0,
        dataUseTags: ["AML", "Screening"],
        lastUpdated: "5d ago",
      },
    ],
  },
];
