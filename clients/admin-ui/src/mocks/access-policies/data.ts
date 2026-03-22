import {
  AccessPolicy,
  ControlGroup,
} from "~/features/access-policies/access-policies.slice";

export const mockControlGroups: ControlGroup[] = [
  {
    key: "eea_uk_gdpr",
    label: "EEA/UK: GDPR Articles 5, 6 — Purpose limitation and lawful basis",
  },
  {
    key: "us_glba_ccpa",
    label: "US: GLBA, CCPA — Financial privacy and consumer rights",
  },
  {
    key: "apac_pdpa_app",
    label: "APAC: PDPA (Singapore), APP (Australia) — Personal data protection",
  },
  {
    key: "global",
    label: "Global: GDPR + GLBA + local equivalents",
  },
];

export const mockAccessPolicies: AccessPolicy[] = [
  {
    id: "policy-1",
    name: "EU Data Access Policy",
    description: "Governs data access requests from EU residents under GDPR",
    control_group: "eea_uk_gdpr",
    yaml: "name: eu_data_access_policy\ndescription: Governs data access requests from EU residents under GDPR\nallow:\n  data_use:\n    operator: any\n    values:\n      - essential\n      - essential.service\n",
    created_at: "2024-01-15T10:00:00Z",
    updated_at: "2024-03-01T14:30:00Z",
  },
  {
    id: "policy-2",
    name: "CCPA Consumer Rights Policy",
    description: "Handles California consumer data requests",
    control_group: "us_glba_ccpa",
    yaml: "name: ccpa_consumer_rights\ndescription: Handles California consumer data requests\ndeny:\n  data_use:\n    operator: any\n    values:\n      - marketing.advertising.third_party\n      - marketing.advertising.third_party.targeted\nunless:\n  any:\n    - consent:\n        preference_key:\n          - ccpa_opt_out\n        value: opt_out\n",
    created_at: "2024-02-01T09:00:00Z",
    updated_at: "2024-02-20T11:00:00Z",
  },
  {
    id: "policy-3",
    name: "Internal Employee Data Policy",
    description: "Controls access to employee personal data",
    control_group: "global",
    yaml: "name: employee_data_policy\ndescription: Controls access to employee personal data\nallow:\n  data_use:\n    operator: any\n    values:\n      - employment\n      - employment.recruitment\n  data_subject:\n    operator: any\n    values:\n      - employee\n      - job_applicant\n",
    created_at: "2024-01-10T08:00:00Z",
    updated_at: "2024-01-10T08:00:00Z",
  },
  {
    id: "policy-4",
    name: "Marketing Analytics Policy",
    description: "Governs use of data for marketing analytics",
    control_group: "us_glba_ccpa",
    yaml: "name: marketing_analytics_policy\ndescription: Governs use of data for marketing analytics\ndeny:\n  data_use:\n    operator: any\n    values:\n      - marketing.advertising.third_party\n  data_category:\n    operator: any\n    values:\n      - user.device.ip_address\n",
    created_at: "2024-03-05T13:00:00Z",
    updated_at: "2024-03-05T13:00:00Z",
  },
];
