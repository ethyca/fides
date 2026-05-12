import { getPrivacyCenterEnvironmentCached } from "~/app/server-utils";

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
  beforeEach(() => {
    mockAsServerSide();
    loadEnvironmentVariablesMock.mockReturnValue({
      USE_API_CONFIG: false,
      LOG_LEVEL: "fatal",
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
      LOG_LEVEL: "fatal",
    });

    await getPrivacyCenterEnvironmentCached({});
    expect(fetchPropertyFromApiMock).toHaveBeenCalledTimes(0);
  });

  it("does call API when env variable USE_API_CONFIG is false but visits another privacy center path ", async () => {
    loadEnvironmentVariablesMock.mockReturnValue({
      USE_API_CONFIG: true,
      LOG_LEVEL: "fatal",
    });

    await getPrivacyCenterEnvironmentCached({ propertyPath: "/myproperty" });
    expect(fetchPropertyFromApiMock).toHaveBeenCalledTimes(1);
  });

  it("does call API when env variable USE_API_CONFIG is true and visits root privacy center ", async () => {
    loadEnvironmentVariablesMock.mockReturnValue({
      USE_API_CONFIG: true,
      LOG_LEVEL: "fatal",
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
