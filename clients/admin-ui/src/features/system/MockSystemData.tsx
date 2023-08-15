import { PrivacyDeclarationResponse, SystemResponse } from "~/types/api";

export const MockDeclarationsData: PrivacyDeclarationResponse[] = [
  {
    name: "Bank Account Information",
    data_categories: ["user.financial.account_number"],
    data_use: "essential.service.payment_processing",
    data_subjects: ["customer"],
    egress: undefined,
    ingress: undefined,
    features: [
      "Match and combine offline data sources",
      "Receive and use automatically-sent device characteristics for identification",
    ],
    legal_basis_for_processing: "Legal obligations", // LegalBasisForProcessingEnum
    impact_assessment_location: undefined,
    retention_period: 180, // string
    processes_special_category_data: true,
    special_category_legal_basis: "Vital interests", // SpecialCategoryLegalBasis
    data_shared_with_third_parties: true,
    third_parties: "undefined",
    shared_categories: [],
    cookies: [],
    id: "pri_123456",
  },
  {
    name: "Signup page",
    data_categories: [
      "user.contact.email",
      "user.contact.address.street",
      "user.contact.address.state",
      "user.contact.name",
    ],
    data_use: "essential",
    data_subjects: ["prospect"],
    dataset_references: ["banking_dataset"],
    egress: undefined,
    ingress: undefined,
    features: [],
    legal_basis_for_processing: "Legitimate interests",
    impact_assessment_location:
      "www.example.com/impact_assessment_banking_company",
    retention_period: undefined,
    processes_special_category_data: false,
    special_category_legal_basis: undefined,
    data_shared_with_third_parties: false,
    third_parties: undefined,
    shared_categories: [],
    cookies: [],
    id: "pri_567890",
  },
];

export const MockSystemData: SystemResponse = {
  fides_key: "banking_app",
  organization_fides_key: "default_organization",
  tags: ["Banking", "CCN"],
  name: "Test Banking App",
  description: "Capture banking data for customers.",
  registry_id: undefined,
  meta: undefined,
  fidesctl_meta: undefined,
  system_type: "system",
  destination: [
    {
      fides_key: "postgres",
      type: "system",
      data_categories: undefined,
    },
  ],
  source: undefined,
  privacy_declarations: MockDeclarationsData, // PrivacyDeclarationResponse[]
  administrating_department: "Accounting",
  vendor_id: "435435345",
  processes_personal_data: true,
  exempt_from_privacy_regulations: false,
  reason_for_exemption: undefined,
  uses_profiling: true,
  legal_basis_for_profiling: "Explicit consent", // LegalBasisForProfilingEnum
  does_international_transfers: true,
  legal_basis_for_transfers: "Standard contractual clauses", // LegalBasisForTransfersEnum
  requires_data_protection_assessments: true,
  dpa_location: "www.example.com/dpia_loc",
  dpa_progress: "started",
  privacy_policy: "www.example.com/privacy_policy",
  legal_name: "My Banking App LLC",
  legal_address: "403 Greenbrier Ln Austin TX 73301",
  responsibility: ["Controller"], // DataResponsibilityTitle
  dpo: "Janice Lee, janicel@example.com",
  joint_controller_info: "Fred Johnson 3042 Toast Town Rd Austin, TX ",
  data_security_practices: undefined,
  connection_configs: undefined,
  cookies: [],
};
