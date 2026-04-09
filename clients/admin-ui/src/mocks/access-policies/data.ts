import {
  AccessPolicy,
  Control,
} from "~/features/access-policies/access-policies.slice";

export const mockControls: Control[] = [
  {
    key: "eea_uk_gdpr",
    label: "EEA/UK: GDPR Articles 6 & 9",
  },
  {
    key: "us_glba_ccpa",
    label: "US: GLBA, CCPA / CPRA",
  },
  {
    key: "apac_pdpa_app",
    label: "APAC: PDPA, APP",
  },
  {
    key: "global",
    label: "Global: GDPR + GLBA + PDPA composite",
  },
];

export const mockAccessPolicies: AccessPolicy[] = [
  {
    id: "policy-1",
    name: "EU Data Access Policy",
    description: "Governs data access requests from EU residents under GDPR",
    controls: ["eea_uk_gdpr"],
    yaml: "fides_key: eu_data_access_policy\nname: EU Data Access Policy\ndescription: Governs data access requests from EU residents under GDPR\nenabled: true\npriority: 100\ncontrols:\n  - eea_uk_gdpr\ndecision: ALLOW\nmatch:\n  data_use:\n    any:\n      - essential\n      - essential.service\n",
    created_at: "2026-01-15T10:00:00Z",
    updated_at: "2026-03-13T14:30:00Z",
  },
  {
    id: "policy-2",
    name: "CCPA Consumer Rights Policy",
    description: "Handles California consumer data requests and opt-out rights",
    controls: ["us_glba_ccpa"],
    yaml: "fides_key: ccpa_consumer_rights\nname: CCPA Consumer Rights Policy\ndescription: Handles California consumer data requests and opt-out rights\nenabled: true\npriority: 200\ncontrols:\n  - us_glba_ccpa\ndecision: DENY\nmatch:\n  data_use:\n    any:\n      - marketing.advertising.third_party\n      - marketing.advertising.third_party.targeted\nunless:\n  - type: consent\n    privacy_notice_key: ccpa_opt_out\n    requirement: opt_out\naction:\n  message: User has opted out of the sale/sharing of their personal data.\n",
    created_at: "2026-02-01T09:00:00Z",
    updated_at: "2026-03-18T11:00:00Z",
  },
  {
    id: "policy-3",
    name: "Internal Employee Data Policy",
    description: "Controls access to employee personal data across HR systems",
    controls: ["global"],
    yaml: "fides_key: employee_data_policy\nname: Internal Employee Data Policy\ndescription: Controls access to employee personal data across HR systems\nenabled: true\npriority: 300\ncontrols:\n  - global\ndecision: ALLOW\nmatch:\n  data_use:\n    any:\n      - employment\n      - employment.recruitment\n  data_subject:\n    any:\n      - employee\n      - job_applicant\n",
    created_at: "2026-03-10T08:00:00Z",
    updated_at: "2026-03-10T08:00:00Z",
  },
  {
    id: "policy-4",
    name: "Marketing Analytics Policy",
    description:
      "Governs use of data for marketing analytics and third-party advertising",
    controls: ["us_glba_ccpa"],
    yaml: "fides_key: marketing_analytics_policy\nname: Marketing Analytics Policy\ndescription: Governs use of data for marketing analytics and third-party advertising\nenabled: true\npriority: 400\ndecision: DENY\nmatch:\n  data_use:\n    any:\n      - marketing.advertising.third_party\n  data_category:\n    any:\n      - user.device.ip_address\naction:\n  message: Third-party advertising with IP address data is not permitted.\n",
    created_at: "2026-03-16T13:00:00Z",
    updated_at: "2026-03-16T13:00:00Z",
  },
  {
    id: "policy-5",
    name: "KYC Data Role Restriction",
    description:
      "Limits access to Know Your Customer identity documents and verification records to compliance and onboarding teams only",
    controls: ["eea_uk_gdpr", "us_glba_ccpa"],
    is_recommendation: true,
    yaml: "fides_key: kyc_data_role_restriction\nname: KYC Data Role Restriction\ndescription: Limits access to KYC identity documents\nenabled: true\npriority: 150\ncontrols:\n  - eea_uk_gdpr\n  - us_glba_ccpa\ndecision: DENY\nmatch:\n  data_use:\n    any:\n      - essential.service.payment_processing\n  data_category:\n    any:\n      - user.government_id\n      - user.financial\naction:\n  message: KYC data access restricted to compliance team.\n",
    created_at: "2026-02-10T09:00:00Z",
    updated_at: "2026-03-23T16:20:00Z",
  },
  {
    id: "policy-6",
    name: "APAC Personal Data Protection",
    description:
      "Enforces PDPA and APP requirements for personal data collected from APAC residents",
    controls: ["apac_pdpa_app"],
    yaml: "fides_key: apac_personal_data\nname: APAC Personal Data Protection\ndescription: Enforces PDPA and APP requirements for APAC residents\nenabled: true\npriority: 250\ncontrols:\n  - apac_pdpa_app\ndecision: ALLOW\nmatch:\n  data_use:\n    any:\n      - essential\n      - essential.service\nunless:\n  - type: geo_location\n    field: environment.geo_location\n    operator: not_in\n    values:\n      - SG\n      - AU\n      - NZ\n",
    created_at: "2026-02-20T07:30:00Z",
    updated_at: "2026-03-26T10:00:00Z",
  },
  {
    id: "policy-7",
    name: "Cardholder Data Access",
    description:
      "Restricts access to detokenized card numbers and CVVs to PCI-certified service accounts within the payment processing environment",
    controls: ["us_glba_ccpa", "global"],
    yaml: "fides_key: cardholder_data_access\nname: Cardholder Data Access\ndescription: PCI-DSS cardholder data restrictions\nenabled: false\npriority: 500\ncontrols:\n  - us_glba_ccpa\n  - global\ndecision: DENY\nmatch:\n  data_category:\n    any:\n      - user.financial.bank_account\n      - user.payment\naction:\n  message: Cardholder data access requires PCI-certified service account.\n",
    created_at: "2026-03-11T11:00:00Z",
    updated_at: "2026-03-11T11:00:00Z",
  },
  {
    id: "policy-8",
    name: "Consent-Gated Profile Access",
    description:
      "Blocks downstream queries on customer profiles where consent preferences have not been recorded or have expired",
    controls: ["eea_uk_gdpr"],
    is_recommendation: true,
    yaml: "fides_key: consent_gated_profiles\nname: Consent-Gated Profile Access\ndescription: Blocks queries on profiles without valid consent\nenabled: false\npriority: 350\ncontrols:\n  - eea_uk_gdpr\ndecision: DENY\nmatch:\n  data_use:\n    any:\n      - marketing\n      - marketing.advertising\nunless:\n  - type: consent\n    privacy_notice_key: marketing_consent\n    requirement: opt_in\naction:\n  message: User has not provided valid marketing consent.\n",
    created_at: "2026-02-28T14:00:00Z",
    updated_at: "2026-03-30T09:30:00Z",
  },
  {
    id: "policy-9",
    name: "SAR Filing Data Access",
    description:
      "Limits access to Suspicious Activity Report records and supporting evidence to designated BSA officers and compliance investigators",
    controls: ["us_glba_ccpa"],
    yaml: "fides_key: sar_filing_access\nname: SAR Filing Data Access\ndescription: BSA/AML SAR access controls\nenabled: true\npriority: 600\ncontrols:\n  - us_glba_ccpa\ndecision: DENY\nmatch:\n  data_use:\n    all:\n      - essential.service.fraud_detection\n  data_subject:\n    any:\n      - customer\naction:\n  message: SAR data restricted to BSA officers.\n",
    created_at: "2026-01-20T08:00:00Z",
    updated_at: "2026-03-20T15:45:00Z",
  },
  {
    id: "policy-10",
    name: "Cross-Border Data Transfer Policy",
    description:
      "Requires explicit data-sharing agreements before granting partner or vendor systems read access to customer data across borders",
    controls: ["eea_uk_gdpr", "apac_pdpa_app"],
    yaml: "fides_key: cross_border_transfer\nname: Cross-Border Data Transfer Policy\ndescription: Cross-border data sharing agreements required\nenabled: true\npriority: 700\ncontrols:\n  - eea_uk_gdpr\n  - apac_pdpa_app\ndecision: DENY\nmatch:\n  data_use:\n    any:\n      - third_party_sharing\nunless:\n  - type: data_flow\n    direction: egress\n    operator: any_of\n    systems:\n      - approved-partner-a\n      - approved-partner-b\naction:\n  message: Cross-border transfer requires approved data sharing agreement.\n",
    created_at: "2026-03-01T10:00:00Z",
    updated_at: "2026-04-02T12:00:00Z",
  },
  {
    id: "policy-11",
    name: "Bulk Financial Export Restriction",
    description:
      "Blocks queries attempting to export more than 10,000 records from account balance and transaction history tables without manager approval",
    controls: ["global"],
    yaml: "fides_key: bulk_financial_export\nname: Bulk Financial Export Restriction\ndescription: Restricts bulk financial data exports\nenabled: true\npriority: 800\ncontrols:\n  - global\ndecision: DENY\nmatch:\n  data_category:\n    any:\n      - user.financial\n      - user.financial.bank_account\naction:\n  message: Bulk financial data export requires manager approval.\n",
    created_at: "2026-03-14T09:00:00Z",
    updated_at: "2026-03-14T09:00:00Z",
  },
  {
    id: "policy-12",
    name: "Singapore PDPA Marketing Consent",
    description:
      "Enforces opt-in consent requirements for marketing communications to Singapore-based data subjects under PDPA",
    controls: ["apac_pdpa_app"],
    is_recommendation: true,
    yaml: "fides_key: sg_pdpa_marketing\nname: Singapore PDPA Marketing Consent\ndescription: PDPA marketing consent enforcement for Singapore\nenabled: true\npriority: 900\ncontrols:\n  - apac_pdpa_app\ndecision: DENY\nmatch:\n  data_use:\n    any:\n      - marketing\n      - marketing.communications\nunless:\n  - type: consent\n    privacy_notice_key: sg_marketing_consent\n    requirement: opt_in\n  - type: geo_location\n    field: environment.geo_location\n    operator: in\n    values:\n      - SG\naction:\n  message: Marketing to SG residents requires explicit PDPA consent.\n",
    created_at: "2026-03-20T07:00:00Z",
    updated_at: "2026-04-05T14:00:00Z",
  },
];
