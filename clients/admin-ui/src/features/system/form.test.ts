import { describe, expect, it } from "@jest/globals";

import { transformFormValuesToSystem } from "~/features/system/form";

describe("transformFormValuesToSystem", () => {
  it("should omit joint controller into and adminitstrating department if empty", () => {
    const formValues = {
      system_type: "",
      fides_key: "",
      tags: [],
      name: "new system",
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
      uses_cookies: false,
      cookie_refresh: false,
      uses_non_cookie_access: false,
      legitimate_interest_disclosure_url: "",
    };

    const payload = transformFormValuesToSystem(formValues);
    expect(payload).not.toHaveProperty("administrating_department");
    expect(payload).not.toHaveProperty("joint_controller_info");
  });

  it("should keep joint controller into and adminitstrating department if not empty", () => {
    const formValues = {
      system_type: "",
      fides_key: "",
      tags: [],
      name: "new system",
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
      administrating_department: "not empty",
      responsibility: [],
      joint_controller_info: "not empty",
      data_security_practices: "",
      privacy_declarations: [],
      data_stewards: "",
      dpo: "",
      uses_cookies: false,
      cookie_refresh: false,
      uses_non_cookie_access: false,
      legitimate_interest_disclosure_url: "",
    };

    const payload = transformFormValuesToSystem(formValues);
    expect(payload).toHaveProperty("administrating_department");
    expect(payload).toHaveProperty("joint_controller_info");
  });
});
