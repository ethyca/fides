import {
  CustomFieldsFormValues,
  CustomFieldValues,
} from "~/features/common/custom-fields";
import { formatKey } from "~/features/datastore-connections/system_portal_config/helpers";
import { DataProtectionImpactAssessment, System } from "~/types/api";

export interface FormValues
  extends Omit<System, "data_protection_impact_assessment">,
    CustomFieldsFormValues {
  data_protection_impact_assessment?: {
    is_required: "true" | "false";
    progress?: DataProtectionImpactAssessment["progress"];
    link?: DataProtectionImpactAssessment["link"];
  };
  customFieldValues?: CustomFieldValues;
}

export const defaultInitialValues: FormValues = {
  system_type: "",
  fides_key: "",
  tags: [],
  name: "",
  description: "",
  dataset_references: [],
  processes_personal_data: true,
  exempt_from_privacy_regulations: false,
  reason_for_exemption: "",
  uses_profiling: false,
  does_international_transfers: false,
  requires_data_protection_assessments: false,
  privacy_policy: "",
  legal_name: "",
  legal_address: "",
  administrating_department: "",
  responsibility: [],
  joint_controller_info: "",
  data_security_practices: "",
  privacy_declarations: [],
};

export const transformSystemToFormValues = (
  system: System,
  customFieldValues?: CustomFieldValues
): FormValues => {
  const { data_protection_impact_assessment: dpia } = system;

  return {
    ...system,
    data_stewards: passedInSystem.data_stewards
      .map((user) => user.username)
      .join(", "),
    data_protection_impact_assessment: {
      ...dpia,
      is_required: dpia?.is_required ? "true" : "false",
    },
    customFieldValues,
  };
};

export const transformFormValuesToSystem = (formValues: FormValues): System => {
  const key = formValues.fides_key
    ? formValues.fides_key
    : formatKey(formValues.name!);

  const privacyPolicy =
    formValues.privacy_policy === "" ? undefined : formValues.privacy_policy;

  if (!formValues.processes_personal_data) {
    return {
      system_type: formValues.system_type,
      fides_key: key,
      name: formValues.name,
      description: formValues.description,
      tags: formValues.tags,
      privacy_declarations: [],
    };
  }

  if (formValues.exempt_from_privacy_regulations) {
    return {
      system_type: formValues.system_type,
      fides_key: key,
      name: formValues.name,
      description: formValues.description,
      tags: formValues.tags,
      privacy_declarations: formValues.privacy_declarations,
      processes_personal_data: formValues.processes_personal_data,
      exempt_from_privacy_regulations:
        formValues.exempt_from_privacy_regulations,
      reason_for_exemption: formValues.reason_for_exemption,
    };
  }

  return {
    system_type: formValues.system_type,
    fides_key: key,
    name: formValues.name,
    description: formValues.description,
    tags: formValues.tags,
    privacy_declarations: formValues.privacy_declarations,
    dataset_references: formValues.dataset_references,
    processes_personal_data: formValues.processes_personal_data,
    exempt_from_privacy_regulations: formValues.exempt_from_privacy_regulations,
    uses_profiling: formValues.uses_profiling,
    legal_basis_for_profiling: formValues.uses_profiling
      ? formValues.legal_basis_for_profiling
      : undefined,
    does_international_transfers: formValues.does_international_transfers,
    legal_basis_for_transfers: formValues.does_international_transfers
      ? formValues.legal_basis_for_transfers
      : undefined,
    requires_data_protection_assessments:
      formValues.requires_data_protection_assessments,
    dpa_location: formValues.requires_data_protection_assessments
      ? formValues.dpa_location
      : undefined,
    privacy_policy: privacyPolicy,
    legal_name: formValues.legal_name,
    legal_address: formValues.legal_address,
    administrating_department: formValues.administrating_department,
    responsibility: formValues.responsibility,
    dpo: formValues.dpo,
    joint_controller_info: formValues.joint_controller_info,
    data_security_practices: formValues.data_security_practices,
  };
};
