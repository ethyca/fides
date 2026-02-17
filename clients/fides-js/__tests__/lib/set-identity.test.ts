import { SetIdentityOptions } from "../../src/lib/consent-types";
import { setIdentity } from "../../src/lib/set-identity";
import { createMockFides } from "../__utils__/test-utils";

jest.mock("../../src/lib/cookie", () => ({
  ...jest.requireActual("../../src/lib/cookie"),
  saveFidesCookie: jest.fn().mockResolvedValue(undefined),
}));

const { saveFidesCookie } = jest.requireMock("../../src/lib/cookie");

describe("setIdentity", () => {
  beforeAll(() => {
    window.fidesDebugger = jest.fn();
  });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("updates cookie.identity.external_id and calls saveFidesCookie", async () => {
    const mockFides = createMockFides();
    await setIdentity.call(mockFides, { external_id: "user-123" });
    expect(mockFides.cookie!.identity.external_id).toBe("user-123");
    expect(saveFidesCookie).toHaveBeenCalledTimes(1);
    expect(saveFidesCookie).toHaveBeenCalledWith(
      mockFides.cookie,
      mockFides.options,
    );
  });

  it("when options.fidesExternalId is set, logs override warning then updates cookie", async () => {
    const mockFides = createMockFides({
      options: {
        ...createMockFides().options,
        fidesExternalId: "initial-id",
      },
    });
    await setIdentity.call(mockFides, { external_id: "new-id" });
    expect(window.fidesDebugger).toHaveBeenCalledWith(
      "setIdentity: overriding existing fidesExternalId from init options with value from setIdentity.",
    );
    expect(mockFides.cookie!.identity.external_id).toBe("new-id");
    expect(saveFidesCookie).toHaveBeenCalledWith(
      mockFides.cookie,
      mockFides.options,
    );
  });

  it("throws when Fides is not initialized (no cookie)", async () => {
    const mockFides = createMockFides({ cookie: undefined });
    await expect(
      setIdentity.call(mockFides, { external_id: "user-123" }),
    ).rejects.toThrow("Fides must be initialized before calling setIdentity.");
    expect(saveFidesCookie).not.toHaveBeenCalled();
  });

  it("throws for reserved key fides_user_device_id", async () => {
    const mockFides = createMockFides();
    await expect(
      setIdentity.call(mockFides, {
        fides_user_device_id: "device-123",
      } as SetIdentityOptions),
    ).rejects.toThrow(
      "fides_user_device_id is reserved and cannot be set via setIdentity.",
    );
    expect(saveFidesCookie).not.toHaveBeenCalled();
  });

  it("throws for verified key email", async () => {
    const mockFides = createMockFides();
    await expect(
      setIdentity.call(mockFides, {
        email: "u@example.com",
      } as SetIdentityOptions),
    ).rejects.toThrow(
      "email and phone_number are verified identity keys and cannot be set via setIdentity.",
    );
    expect(saveFidesCookie).not.toHaveBeenCalled();
  });

  it("throws for verified key phone_number", async () => {
    const mockFides = createMockFides();
    await expect(
      setIdentity.call(mockFides, {
        phone_number: "+15551234567",
      } as SetIdentityOptions),
    ).rejects.toThrow(
      "email and phone_number are verified identity keys and cannot be set via setIdentity.",
    );
    expect(saveFidesCookie).not.toHaveBeenCalled();
  });

  it("throws for unsupported custom key", async () => {
    const mockFides = createMockFides();
    await expect(
      setIdentity.call(mockFides, {
        custom_key: "value",
      } as SetIdentityOptions),
    ).rejects.toThrow(
      "Only external_id is supported. Unsupported key: custom_key.",
    );
    expect(saveFidesCookie).not.toHaveBeenCalled();
  });

  it("throws when external_id is empty string", async () => {
    const mockFides = createMockFides();
    await expect(
      setIdentity.call(mockFides, { external_id: "" }),
    ).rejects.toThrow(
      "external_id cannot be empty or whitespace-only. Omit the key to leave identity unchanged.",
    );
    expect(saveFidesCookie).not.toHaveBeenCalled();
  });

  it("throws when external_id is whitespace-only", async () => {
    const mockFides = createMockFides();
    await expect(
      setIdentity.call(mockFides, { external_id: "   \t\n  " }),
    ).rejects.toThrow(
      "external_id cannot be empty or whitespace-only. Omit the key to leave identity unchanged.",
    );
    expect(saveFidesCookie).not.toHaveBeenCalled();
  });

  it("trims external_id before saving", async () => {
    const mockFides = createMockFides();
    await setIdentity.call(mockFides, { external_id: "  user-456  " });
    expect(mockFides.cookie!.identity.external_id).toBe("user-456");
    expect(saveFidesCookie).toHaveBeenCalledTimes(1);
  });

  it("does nothing and does not call saveFidesCookie when identity is empty", async () => {
    const mockFides = createMockFides();
    await setIdentity.call(mockFides, {});
    expect(saveFidesCookie).not.toHaveBeenCalled();
  });
});
