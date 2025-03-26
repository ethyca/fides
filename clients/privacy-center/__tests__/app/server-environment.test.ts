import { produce } from "immer";

import { validateConfig } from "~/app/server-environment";
import { getPrivacyCenterEnvironmentCached } from "~/app/server-utils";
import customFields from "~/config/examples/customFields.json";
import fullJson from "~/config/examples/full.json";
import minimalJson from "~/config/examples/minimal.json";
import v2ConsentJson from "~/config/examples/v2Consent.json";

describe("validateConfig", () => {
  const testCases = [
    {
      name: "no consent options",
      config: minimalJson,
      expected: {
        isValid: true,
      },
    },
    {
      name: "valid consent options",
      config: fullJson,
      expected: {
        isValid: true,
      },
    },
    {
      name: "multiple executable consent options",
      config: produce(fullJson, (draftConfig) => {
        draftConfig.consent.consentOptions[0].executable = true;
        draftConfig.consent.consentOptions[1].executable = true;
      }),
      expected: {
        isValid: false,
        message: "Cannot have more than one consent option be executable",
      },
    },
    {
      name: "v2 consent config",
      config: produce(v2ConsentJson, (draftConfig) => {
        draftConfig.consent.page.consentOptions[0].executable = true;
      }),
      expected: {
        isValid: true,
      },
    },
    {
      name: "multiple executable v2 consent options",
      config: produce(v2ConsentJson, (draftConfig) => {
        draftConfig.consent.page.consentOptions[0].executable = true;
        draftConfig.consent.page.consentOptions[1].executable = true;
      }),
      expected: {
        isValid: false,
        message: "Cannot have more than one consent option be executable",
      },
    },
    {
      name: "hidden fields with missing default values",
      config: customFields,
      expected: {
        isValid: false,
        message:
          "A default_value or query_param_key is required for hidden field(s) 'tenant_id' in the action with policy_key 'default_access_policy', 'tenant_id' in the action with policy_key 'default_erasure_policy'",
      },
    },
  ];

  testCases.forEach((tc) => {
    test(tc.name, () => {
      expect(validateConfig(tc.config)).toMatchObject(tc.expected);
    });
  });
});

const mockAsServerSide = () => {
  jest
    .spyOn(globalThis, "window", "get")
    .mockImplementation(() => undefined as any);
};

const fetchPropertyFromApiMock = jest.fn();
const loadEnvironmentVariablesMock = jest.fn();
const lookupGeolocationServerSideMock = jest.fn();

jest.mock(
  "~/app/server-utils/fetchPropertyFromApi",
  () => (arg: any) => fetchPropertyFromApiMock(arg),
);

jest.mock(
  "~/app/server-utils/lookupGeolocationServerSide",
  () => (arg: any) => lookupGeolocationServerSideMock(arg),
);

jest.mock(
  "~/app/server-utils/loadEnvironmentVariables",
  () => (arg: any) => loadEnvironmentVariablesMock(arg),
);

describe("loadPrivacyCenterEnvironment", () => {
  beforeAll(() => {
    (globalThis as any).fidesDebugger = () => {};
  });
  beforeEach(() => {
    mockAsServerSide();
    loadEnvironmentVariablesMock.mockReturnValue({
      USE_API_CONFIG: false,
    });
    lookupGeolocationServerSideMock.mockResolvedValue({
      location: "us-ca",
      country: "us",
      region: "ca",
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it("doesn't call API when env variable USE_API_CONFIG is false and visits root privacy center ", async () => {
    loadEnvironmentVariablesMock.mockReturnValue({
      USE_API_CONFIG: false,
    });

    await getPrivacyCenterEnvironmentCached({});
    expect(fetchPropertyFromApiMock).toHaveBeenCalledTimes(0);
  });

  it("does call API when env variable USE_API_CONFIG is false but visits another privacy center path ", async () => {
    loadEnvironmentVariablesMock.mockReturnValue({
      USE_API_CONFIG: true,
    });

    await getPrivacyCenterEnvironmentCached({ propertyPath: "/myproperty" });
    expect(fetchPropertyFromApiMock).toHaveBeenCalledTimes(1);
  });

  it("does call API when env variable USE_API_CONFIG is true and visits root privacy center ", async () => {
    loadEnvironmentVariablesMock.mockReturnValue({
      USE_API_CONFIG: true,
    });

    await getPrivacyCenterEnvironmentCached({});
    expect(fetchPropertyFromApiMock).toHaveBeenCalledTimes(1);
  });

  it("calls fetchPropertyFromApi with the correct path when called with a path", async () => {
    await getPrivacyCenterEnvironmentCached({ propertyPath: "mycustompath" });
    expect(fetchPropertyFromApiMock).toHaveBeenCalledTimes(1);
    expect(fetchPropertyFromApiMock).toHaveBeenCalledWith(
      expect.objectContaining({
        path: "mycustompath",
      }),
    );
  });

  it("returns property config and stylesheet if a property was found by it's path", async () => {
    fetchPropertyFromApiMock.mockReturnValue({
      privacy_center_config: { some: "config" },
      stylesheet: "some stylesheet",
    });

    const result = await getPrivacyCenterEnvironmentCached({
      propertyPath: "mycustompath",
    });
    expect(fetchPropertyFromApiMock).toHaveBeenCalledTimes(1);

    expect(result.config).toEqual({ some: "config" });
    expect(result.styles).toEqual("some stylesheet");
  });
});
