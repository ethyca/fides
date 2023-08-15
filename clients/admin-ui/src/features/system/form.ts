import {
  CustomFieldsFormValues,
  CustomFieldValues,
} from "~/features/common/custom-fields";
import { formatKey } from "~/features/datastore-connections/system_portal_config/helpers";
import { DEFAULT_ORGANIZATION_FIDES_KEY } from "~/features/organization";
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

// export const defaultInitialValues: FormValues = {
//   description: "",
//   fides_key: "",
//   name: "",
//   organization_fides_key: DEFAULT_ORGANIZATION_FIDES_KEY,
//   tags: [],
//   system_type: "",
//   privacy_declarations: [],
//   data_responsibility_title: undefined,
//   administrating_department: "",
//   third_country_transfers: [],
//   joint_controller: {
//     name: "",
//     email: "",
//     address: "",
//     phone: "",
//   },
//   data_protection_impact_assessment: {
//     is_required: "false",
//     progress: "",
//     link: "",
//   },
// };

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
    privacy_policy: formValues.privacy_policy,
    legal_name: formValues.legal_name,
    legal_address: formValues.legal_address,
    administrating_department: formValues.administrating_department,
    responsibility: formValues.responsibility,
    dpo: formValues.dpo,
    joint_controller_info: formValues.joint_controller_info,
    data_security_practices: formValues.data_security_practices,
  };

  // return {
  //   // Fields that are preserved by the form:
  //   data_responsibility_title: formValues.data_responsibility_title,
  //   description: formValues.description,
  //   egress: formValues.egress,
  //   fides_key: formatKey(formValues.name!),
  //   ingress: formValues.ingress,
  //   name: formValues.name,
  //   organization_fides_key: formValues.organization_fides_key,
  //   privacy_declarations: formValues.privacy_declarations,
  //   system_type: formValues.system_type,
  //   tags: formValues.tags,
  //   third_country_transfers: formValues.third_country_transfers,

  //   // Fields that need transformation:
  //   data_protection_impact_assessment: impactAssessment,
  //   joint_controller: jointController,
  //   administrating_department:
  //     formValues.administrating_department === ""
  //       ? undefined
  //       : formValues.administrating_department,
  // };
};
