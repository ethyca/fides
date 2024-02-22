import {
  getWindowObjFromPath,
  isPrivacyExperience,
} from "~/lib/consent-utils";

// TODO: update to shared fixture with future i18n tests
const MOCK_EXPERIENCE = {
  id: "132345243",
  region: "us_ca",
  show_banner: true,
  component: "overlay",
  created_at: "2023-04-24T21:29:08.870351+00:00",
  updated_at: "2023-04-24T21:29:08.870351+00:00",
  experience_config: {
    accept_button_label: "Accept Test",
    acknowledge_button_label: "OK",
    banner_enabled: "enabled_where_required",
    disabled: false,
    description:
      "We use cookies and similar methods to recognize visitors and remember their preferences. We also use them to measure ad campaign effectiveness, target ads and analyze site traffic. Learn more about these methods, including how to manage them, by clicking ‘Manage Preferences.’ By clicking ‘accept’ you consent to the of these methods by us and our third parties. By clicking ‘reject’ you decline the use of these methods.",
    reject_button_label: "Reject Test",
    is_default: false,
    save_button_label: "Save test",
    title: "Manage your consent",
    component: "overlay",
    version: 2.0,
    privacy_policy_link_label: "Privacy policy",
    privacy_policy_url: "https://privacy.ethyca.com/",
    privacy_preferences_link_label: "Manage preferences",
    created_at: "2023-04-24T21:29:08.870351+00:00",
    updated_at: "2023-04-24T21:29:08.870351+00:00",
    id: "2348571y34",
    regions: ["us_ca"],
  },
  privacy_notices: [
    {
      name: "Test privacy notice",
      disabled: false,
      origin: "12435134",
      description: "a test sample privacy notice configuration",
      internal_description:
        "a test sample privacy notice configuration for internal use",
      regions: ["us_ca"],
      consent_mechanism: "opt_in",
      default_preference: "opt_out",
      current_preference: null,
      outdated_preference: null,
      has_gpc_flag: true,
      data_uses: ["advertising", "third_party_sharing"],
      enforcement_level: "system_wide",
      displayed_in_overlay: true,
      displayed_in_api: true,
      displayed_in_privacy_center: false,
      id: "pri_4bed96d0-b9e3-4596-a807-26b783836374",
      created_at: "2023-04-24T21:29:08.870351+00:00",
      updated_at: "2023-04-24T21:29:08.870351+00:00",
      version: 1.0,
      privacy_notice_history_id: "pri_b09058a7-9f54-4360-8da5-4521e8975d4f",
      notice_key: "advertising",
      cookies: [{ name: "testCookie", path: "/", domain: null }],
    },
    {
      name: "Essential",
      description:
        "Notify the user about data processing activities that are essential to your services functionality. Typically consent is not required for this.",
      regions: ["us_ca"],
      consent_mechanism: "notice_only",
      default_preference: "opt_in",
      current_preference: null,
      outdated_preference: null,
      has_gpc_flag: true,
      data_uses: ["provide.service"],
      enforcement_level: "system_wide",
      displayed_in_overlay: true,
      displayed_in_api: true,
      displayed_in_privacy_center: false,
      id: "pri_4bed96d0-b9e3-4596-a807-26b783836375",
      created_at: "2023-04-24T21:29:08.870351+00:00",
      updated_at: "2023-04-24T21:29:08.870351+00:00",
      version: 1.0,
      privacy_notice_history_id: "pri_b09058a7-9f54-4360-8da5-4521e8975d4e",
      notice_key: "essential",
      cookies: [],
    },
  ],
};

describe("isPrivacyExperience", () => {
  it.each([
    { label: "undefined", obj: undefined, expected: false },
    { label: "a number", obj: 7, expected: false },
    { label: "an object", obj: { foo: "bar" }, expected: false },
    { label: "a string", obj: "foo", expected: false },
    { label: "an empty object", obj: {}, expected: true },
    {
      label: "an object with 'id'",
      obj: { id: "123456", foo: "bar" },
      expected: true,
    },
    {
      label: "a full 'experience' object",
      obj: MOCK_EXPERIENCE,
      expected: true,
    },
  ])("returns $expected when input is $label", ({ obj, expected }) => {
    expect(isPrivacyExperience(obj as any)).toBe(expected);
  });
});

describe("getWindowObjFromPath", () => {
  let windowSpy: any;

  beforeEach(() => {
    windowSpy = jest.spyOn(window, "window", "get");
  });

  afterEach(() => {
    windowSpy.mockRestore();
  });
  const windowMock1 = {
    fides_overrides: {
      hello: "something",
    },
  };
  const windowMock2 = {
    overrides: {
      fides: {
        hello: "something-else",
      },
    },
  };
  it.each([
    {
      label: "path does not exist",
      path: ["window", "nonexistent-path"],
      window: windowMock1,
      expected: undefined,
    },
    {
      label: "nested path does not exist",
      path: ["window", "nonexistent-path", "nested"],
      window: windowMock1,
      expected: undefined,
    },
    {
      label: "path is one level deep",
      path: ["window", "fides_overrides"],
      window: windowMock1,
      expected: { hello: "something" },
    },
    {
      label: "path is two levels deep",
      path: ["window", "overrides", "fides"],
      window: windowMock2,
      expected: { hello: "something-else" },
    },
  ])(
    "returns $expected when path is $path and window is $window",
    ({ path, window, expected }) => {
      windowSpy.mockImplementation(() => window);
      expect(getWindowObjFromPath(path as any)).toStrictEqual(expected);
    }
  );
});
