import { DEFAULT_ORGANIZATION_FIDES_KEY } from "~/features/organization";
import { DataProtectionImpactAssessment, System } from "~/types/api";

export interface FormValues
  extends Omit<System, "data_protection_impact_assessment"> {
  data_protection_impact_assessment?: {
    is_required: "true" | "false";
    progress?: DataProtectionImpactAssessment["progress"];
    link?: DataProtectionImpactAssessment["link"];
  };
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

export const transformSystemToFormValues = (system: System): FormValues => {
  const { data_protection_impact_assessment: dpia } = system;
  return {
    ...system,
    data_protection_impact_assessment: {
      ...dpia,
      is_required: dpia?.is_required ? "true" : "false",
    },
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
    ...formValues,
    organization_fides_key: DEFAULT_ORGANIZATION_FIDES_KEY,
    data_protection_impact_assessment: impactAssessment,
    joint_controller: jointController,
    administrating_department:
      formValues.administrating_department === ""
        ? undefined
        : formValues.administrating_department,
  };
};
