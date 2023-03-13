import { CustomFieldsFormValues } from "~/features/common/custom-fields";
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
  definitionIdToCustomFieldValue?: Record<string, string | string[]>;
}

export const defaultInitialValues: FormValues = {
  description: "",
  fides_key: "",
  name: "",
  organization_fides_key: DEFAULT_ORGANIZATION_FIDES_KEY,
  tags: [],
  system_type: "",
  privacy_declarations: [],
  data_responsibility_title: undefined,
  administrating_department: "",
  third_country_transfers: [],
  system_dependencies: [],
  joint_controller: {
    name: "",
    email: "",
    address: "",
    phone: "",
  },
  data_protection_impact_assessment: {
    is_required: "false",
    progress: "",
    link: "",
  },
};

export const transformSystemToFormValues = (
  system: System,
  definitionIdToCustomField?: Map<any, any>
): FormValues => {
  const { data_protection_impact_assessment: dpia } = system;
  const customFields: Record<string, string | string[]> = {};

  if (definitionIdToCustomField) {
    definitionIdToCustomField.forEach((value, key) => {
      customFields[key] = value.value;
    });
  }

  return {
    ...system,
    data_protection_impact_assessment: {
      ...dpia,
      is_required: dpia?.is_required ? "true" : "false",
    },
    definitionIdToCustomFieldValue: customFields,
  };
};

export const transformFormValuesToSystem = (formValues: FormValues): System => {
  const hasImpactAssessment =
    formValues.data_protection_impact_assessment?.is_required === "true";
  const impactAssessment = hasImpactAssessment
    ? { ...formValues.data_protection_impact_assessment, is_required: true }
    : undefined;
  const hasJointController = formValues.joint_controller
    ? !Object.values(formValues.joint_controller).every((value) => value === "")
    : false;
  const jointController = hasJointController
    ? formValues.joint_controller
    : undefined;

  return {
    // Fields that are preserved by the form:
    data_responsibility_title: formValues.data_responsibility_title,
    description: formValues.description,
    egress: formValues.egress,
    fides_key: formValues.fides_key,
    ingress: formValues.ingress,
    name: formValues.name,
    organization_fides_key: formValues.organization_fides_key,
    privacy_declarations: formValues.privacy_declarations,
    system_dependencies: formValues.system_dependencies,
    system_type: formValues.system_type,
    tags: formValues.tags,
    third_country_transfers: formValues.third_country_transfers,

    // Fields that need transformation:
    data_protection_impact_assessment: impactAssessment,
    joint_controller: jointController,
    administrating_department:
      formValues.administrating_department === ""
        ? undefined
        : formValues.administrating_department,
  };
};
