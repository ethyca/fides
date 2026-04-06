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
    yaml: "fides_key: eu_data_access_policy\nname: EU Data Access Policy\ndescription: Governs data access requests from EU residents under GDPR\ncontrols:\n  - eea_uk_gdpr\ndecision: ALLOW\nmatch:\n  data_use:\n    any:\n      - essential\n      - essential.service\n",
    created_at: "2024-01-15T10:00:00Z",
    updated_at: "2024-03-01T14:30:00Z",
  },
  {
    id: "policy-2",
    name: "CCPA Consumer Rights Policy",
    description: "Handles California consumer data requests",
    controls: ["us_glba_ccpa"],
    yaml: "fides_key: ccpa_consumer_rights\nname: CCPA Consumer Rights Policy\ndescription: Handles California consumer data requests\ncontrols:\n  - us_glba_ccpa\ndecision: DENY\nmatch:\n  data_use:\n    any:\n      - marketing.advertising.third_party\n      - marketing.advertising.third_party.targeted\nunless:\n  - type: consent\n    privacy_notice_key: ccpa_opt_out\n    requirement: opt_out\naction:\n  message: User has opted out of the sale/sharing of their personal data.\n",
    created_at: "2024-02-01T09:00:00Z",
    updated_at: "2024-02-20T11:00:00Z",
  },
  {
    id: "policy-3",
    name: "Internal Employee Data Policy",
    description: "Controls access to employee personal data",
    controls: ["global"],
    yaml: "fides_key: employee_data_policy\nname: Internal Employee Data Policy\ndescription: Controls access to employee personal data\ncontrols:\n  - global\ndecision: ALLOW\nmatch:\n  data_use:\n    any:\n      - employment\n      - employment.recruitment\n  data_subject:\n    any:\n      - employee\n      - job_applicant\n",
    created_at: "2024-01-10T08:00:00Z",
    updated_at: "2024-01-10T08:00:00Z",
  },
  {
    id: "policy-4",
    name: "Marketing Analytics Policy",
    description: "Governs use of data for marketing analytics",
    controls: ["us_glba_ccpa"],
    yaml: "fides_key: marketing_analytics_policy\nname: Marketing Analytics Policy\ndescription: Governs use of data for marketing analytics\npriority: 200\ndecision: DENY\nmatch:\n  data_use:\n    any:\n      - marketing.advertising.third_party\n  data_category:\n    any:\n      - user.device.ip_address\naction:\n  message: Third-party advertising with IP address data is not permitted.\n",
    created_at: "2024-03-05T13:00:00Z",
    updated_at: "2024-03-05T13:00:00Z",
  },
];
