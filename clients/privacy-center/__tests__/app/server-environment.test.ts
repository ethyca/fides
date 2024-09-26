import { produce } from "immer";

import {
  loadPrivacyCenterEnvironment,
  validateConfig,
} from "~/app/server-environment";
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

const mockAsClientSide = () => {
  jest.spyOn(globalThis, "window", "get").mockImplementation(() => ({}) as any);
};

const getPropertyFromUrlMock = jest.fn();
const loadEnvironmentVariablesMock = jest.fn();

jest.mock(
  "~/app/server-utils/getPropertyFromUrl",
  () => (arg: any) => getPropertyFromUrlMock(arg),
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
      CUSTOM_PROPERTIES: true,
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it("throws when trying to run in window environment", () => {
    mockAsClientSide();
    expect(() => loadPrivacyCenterEnvironment({})).rejects.toThrow();
  });

  it("doesn't fetch properties when env variable CUSTOM_PROPERTIES is false", () => {
    loadEnvironmentVariablesMock.mockReturnValue({
      CUSTOM_PROPERTIES: false,
    });

    loadPrivacyCenterEnvironment({ customPropertyPath: "mycustompath" });
    expect(getPropertyFromUrlMock).toHaveBeenCalledTimes(0);
  });

  it("calls getPropertyFromUrl with the correct path when called with a path", () => {
    loadPrivacyCenterEnvironment({ customPropertyPath: "mycustompath" });
    expect(getPropertyFromUrlMock).toHaveBeenCalledTimes(1);
    expect(getPropertyFromUrlMock).toHaveBeenCalledWith({
      customPropertyPath: "mycustompath",
    });
  });

  it("returns property config and stylesheet if a property was found by it's path", async () => {
    getPropertyFromUrlMock.mockReturnValue({
      privacy_center_config: { some: "config" },
      stylesheet: "some stylesheet",
    });

    const result = await loadPrivacyCenterEnvironment({
      customPropertyPath: "mycustompath",
    });
    expect(getPropertyFromUrlMock).toHaveBeenCalledTimes(1);

    expect(result.config).toEqual({ some: "config" });
    expect(result.styles).toEqual("some stylesheet");
  });
});
