import { NewSystem } from "./newSystemMockType";

export interface FormValues extends NewSystem {}

export const newDefaultInitialValues: FormValues = {
  fides_key: "",
  organization_fides_key: "",
  tags: [],
  name: "",
  description: "",
  registry_id: "",
  meta: "",
  fidesctl_meta: "",
  system_type: "",
  destination: [],
  source: [],
  privacy_declarations: [],
  administrating_department: "",
  vendor_id: "",
  processes_personal_data: true,
  exempt_from_privacy_regulations: false,
  reason_for_exemption: "",
  uses_profiling: false,
  legal_basis_for_profiling: "",
  does_international_transfers: false,
  legal_basis_for_transfers: "",
  requires_data_protection_assessments: false,
  dpa_location: "",
  dpa_progress: "",
  privacy_policy: "",
  legal_name: "",
  legal_address: "",
  responsibility: [],
  dpo: "",
  joint_controller_info: "",
  data_security_practices: [],
  connection_configs: [],
  cookies: [],
};

export const transformNewSystemToFormValues = (
  system: NewSystem
): FormValues => {
  return system;
};
