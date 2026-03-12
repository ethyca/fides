import { AccessPolicy } from "~/features/access-policies/access-policies.slice";

export const mockAccessPolicies: AccessPolicy[] = [
  {
    id: "policy-1",
    name: "EU Data Access Policy",
    description: "Governs data access requests from EU residents under GDPR",
    control_group: "compliance",
    yaml: "name: eu_data_access_policy\ndescription: GDPR access policy\nrules:\n  - action: allow\n    condition: location == 'EU'\n",
    created_at: "2024-01-15T10:00:00Z",
    updated_at: "2024-03-01T14:30:00Z",
  },
  {
    id: "policy-2",
    name: "CCPA Consumer Rights Policy",
    description: "Handles California consumer data requests",
    control_group: "compliance",
    yaml: "name: ccpa_consumer_rights\ndescription: CCPA policy\nrules:\n  - action: allow\n    condition: state == 'CA'\n",
    created_at: "2024-02-01T09:00:00Z",
    updated_at: "2024-02-20T11:00:00Z",
  },
  {
    id: "policy-3",
    name: "Internal Employee Data Policy",
    description: "Controls access to employee personal data",
    control_group: "hr",
    yaml: "name: employee_data_policy\ndescription: HR data governance\nrules:\n  - action: restrict\n    condition: department != 'HR'\n",
    created_at: "2024-01-10T08:00:00Z",
    updated_at: "2024-01-10T08:00:00Z",
  },
  {
    id: "policy-4",
    name: "Marketing Analytics Policy",
    description: "Governs use of data for marketing analytics",
    control_group: "marketing",
    created_at: "2024-03-05T13:00:00Z",
    updated_at: "2024-03-05T13:00:00Z",
  },
];
