import {
  CustomFieldsFormValues,
  CustomFieldValues,
} from "~/features/common/custom-fields";
import { formatKey } from "~/features/datastore-connections/system_portal_config/helpers";
import { System } from "~/types/api";

export type FormValues = System &
  CustomFieldsFormValues & {
    customFieldValues?: CustomFieldValues;
    data_stewards: string;
  };

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
  data_stewards: "",
  dpo: "",
  cookie_max_age_seconds: undefined,
  uses_cookies: false,
  cookie_refresh: false,
  uses_non_cookie_access: false,
  legitimate_interest_disclosure_url: "",
};

export const transformSystemToFormValues = (
  system: System,
  customFieldValues?: CustomFieldValues,
): FormValues => {
  // @ts-ignore
  const dataStewards = system?.data_stewards
    ?.map((user: any) => user.username)
    .join(", ");

  return {
    ...system,
    customFieldValues,
    description: system.description ? system.description : "",
    legal_address: system.legal_address ? system.legal_address : "",
    dpo: system.dpo ? system.dpo : "",
    // It looks like number input uses strings under the hood
    // The backend will parse the string into a number
    // @ts-ignore
    cookie_max_age_seconds: system.cookie_max_age_seconds
      ? system.cookie_max_age_seconds
      : "",
    legitimate_interest_disclosure_url:
      system.legitimate_interest_disclosure_url
        ? system.legitimate_interest_disclosure_url
        : "",
    vendor_deleted_date: system.vendor_deleted_date
      ? system.vendor_deleted_date
      : undefined,
    privacy_policy: system.privacy_policy ? system.privacy_policy : "",
    data_security_practices: system.data_security_practices
      ? system.data_security_practices
      : "",
    // these fields require membership in their enums and won't let you assign them a blank string normally
    // they're transformed back into appropriate systems on submission by transformFormValuesToSystem below
    // @ts-ignore
    legal_basis_for_profiling: system.legal_basis_for_profiling
      ? system.legal_basis_for_profiling
      : "",
    // @ts-ignore
    legal_basis_for_transfers: system.legal_basis_for_transfers
      ? system.legal_basis_for_transfers
      : "",
    data_stewards: dataStewards,
  };
};

export const transformFormValuesToSystem = (formValues: FormValues): System => {
  const key = formValues.fides_key
    ? formValues.fides_key
    : formatKey(formValues.name!);

  const privacyPolicy =
    formValues.privacy_policy === "" ? undefined : formValues.privacy_policy;

  let payload: System = {
    system_type: formValues.system_type,
    fides_key: key,
    name: formValues.name,
    description: formValues.description ? formValues.description : "",
    dataset_references: formValues.dataset_references,
    tags: formValues.tags,
    processes_personal_data: formValues.processes_personal_data,
    exempt_from_privacy_regulations: formValues.exempt_from_privacy_regulations,
    reason_for_exemption: formValues.exempt_from_privacy_regulations
      ? formValues.reason_for_exemption
      : undefined,
    privacy_declarations: formValues.processes_personal_data
      ? formValues.privacy_declarations
      : [],
    vendor_id: formValues.vendor_id,
    ingress: formValues.ingress,
    egress: formValues.egress,
    meta: formValues.meta,
    fidesctl_meta: formValues.fidesctl_meta,
    organization_fides_key: formValues.organization_fides_key,
    dpa_progress: formValues.dpa_progress,
    previous_vendor_id: formValues.previous_vendor_id,
    cookies: formValues.cookies,
    cookie_max_age_seconds: formValues.cookie_max_age_seconds
      ? formValues.cookie_max_age_seconds
      : undefined,
    uses_cookies: formValues.uses_cookies,
    cookie_refresh: formValues.cookie_refresh,
    uses_non_cookie_access: formValues.uses_non_cookie_access,
    legitimate_interest_disclosure_url:
      formValues.legitimate_interest_disclosure_url
        ? formValues.legitimate_interest_disclosure_url
        : undefined,
    vendor_deleted_date: formValues.vendor_deleted_date
      ? formValues.vendor_deleted_date
      : undefined,
  };

  if (!formValues.processes_personal_data) {
    return payload;
  }

  payload = {
    ...payload,
    dataset_references: formValues.dataset_references,
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
    responsibility: formValues.responsibility,
    dpo: formValues.dpo,
    data_security_practices: formValues.data_security_practices,
  };

  if (formValues.administrating_department) {
    payload.administrating_department = formValues.administrating_department;
  }

  if (formValues.joint_controller_info) {
    payload.joint_controller_info = formValues.joint_controller_info;
  }

  return payload;
};
