import { CmpApi } from "@iabgpp/cmpapi";

import { FidesCookie } from "../../../src/lib/consent-types";
import { saveFidesCookie } from "../../../src/lib/cookie";
import { dispatchFidesEvent } from "../../../src/lib/events";

jest.mock("../../../src/lib/cookie", () => ({
  saveFidesCookie: jest.fn(),
}));

// Mock performance API
Object.defineProperty(global, "performance", {
  value: {
    mark: jest.fn(),
    measure: jest.fn(),
    getEntriesByName: jest.fn(),
    clearMarks: jest.fn(),
    clearMeasures: jest.fn(),
  },
  writable: true,
});

describe("GPP cookie handling", () => {
  let mockCmpApi: jest.Mocked<CmpApi>;
  const mockGppString = "DBABLA~BVAUAAAAAWA.QA";

  beforeEach(() => {
    // Mock fidesDebugger
    (window as any).fidesDebugger = jest.fn();

    // Mock GPP API
    mockCmpApi = {
      getGppString: jest.fn().mockReturnValue(mockGppString),
      addEventListener: jest.fn(),
      fireEvent: jest.fn(),
    } as unknown as jest.Mocked<CmpApi>;

    // Set up window.__gpp
    type GppCallback = (
      gppData: { gppString: string },
      success: boolean,
    ) => void;
    // eslint-disable-next-line no-underscore-dangle
    (window as any).__gpp = jest
      .fn()
      .mockImplementation((command: string, callback: GppCallback) => {
        if (command === "getGPPData") {
          callback({ gppString: mockGppString }, true);
        }
      });

    window.Fides = {
      cookie: {
        consent: {},
        fides_meta: {},
        identity: {},
        tcf_consent: {},
      } as FidesCookie,
      options: {
        tcfEnabled: false,
        base64Cookie: false,
        gppEnabled: true,
      },
      gppApi: mockCmpApi,
    } as any;

    // Mock the event handler that updates GPP string
    const updateHandler = () => {
      const gppString = mockCmpApi.getGppString();
      if (!gppString) {
        return;
      }

      if (!window.Fides.cookie) {
        return;
      }
      const parts = (window.Fides.cookie.fides_string || ",,").split(",");
      parts[2] = gppString;
      window.Fides.cookie.fides_string = parts.join(",");
      saveFidesCookie(window.Fides.cookie, false);
    };
    window.addEventListener("FidesUpdated", updateHandler);

    // Store handler for cleanup
    (window as any).testEventHandlers = {
      updateHandler,
    };
  });

  afterEach(() => {
    jest.clearAllMocks();
    // eslint-disable-next-line no-underscore-dangle
    delete (window as any).__gpp;
    // Clean up event listeners
    const handlers = (window as any).testEventHandlers;
    if (handlers?.updateHandler) {
      window.removeEventListener("FidesUpdated", handlers.updateHandler);
    }
    delete (window as any).testEventHandlers;
  });

  it("stores GPP string in cookie for non-TCF implementation", () => {
    dispatchFidesEvent(
      "FidesUpdated",
      {
        consent: {},
        fides_meta: {},
        identity: {},
        tcf_consent: {},
      },
      false,
      {},
    );

    expect(window.Fides.cookie?.fides_string).toBe(",,DBABLA~BVAUAAAAAWA.QA");
    expect(saveFidesCookie).toHaveBeenCalledWith(window.Fides.cookie, false);
  });

  it("appends GPP string to existing fides_string when TCF is enabled", () => {
    window.Fides.options.tcfEnabled = true;
    window.Fides.cookie!.fides_string = "TCF_STRING,AC_STRING";

    dispatchFidesEvent(
      "FidesUpdated",
      {
        consent: {},
        fides_meta: {},
        identity: {},
        tcf_consent: {},
      },
      false,
      {},
    );

    expect(window.Fides.cookie?.fides_string).toBe(
      "TCF_STRING,AC_STRING,DBABLA~BVAUAAAAAWA.QA",
    );
    expect(saveFidesCookie).toHaveBeenCalledWith(window.Fides.cookie, false);
  });

  it("handles missing parts in fides_string when TCF is enabled", () => {
    window.Fides.options.tcfEnabled = true;
    window.Fides.cookie!.fides_string = "TCF_STRING";

    dispatchFidesEvent(
      "FidesUpdated",
      {
        consent: {},
        fides_meta: {},
        identity: {},
        tcf_consent: {},
      },
      false,
      {},
    );

    expect(window.Fides.cookie?.fides_string).toBe(
      "TCF_STRING,,DBABLA~BVAUAAAAAWA.QA",
    );
    expect(saveFidesCookie).toHaveBeenCalledWith(window.Fides.cookie, false);
  });

  it("handles empty GPP string", () => {
    mockCmpApi.getGppString.mockReturnValue("");

    dispatchFidesEvent(
      "FidesUpdated",
      {
        consent: {},
        fides_meta: {},
        identity: {},
        tcf_consent: {},
      },
      false,
      {},
    );

    expect(window.Fides.cookie?.fides_string).toBeUndefined();
    expect(saveFidesCookie).not.toHaveBeenCalled();
  });

  it("handles undefined cookie", () => {
    window.Fides.cookie = undefined;

    dispatchFidesEvent(
      "FidesUpdated",
      {
        consent: {},
        fides_meta: {},
        identity: {},
        tcf_consent: {},
      },
      false,
      {},
    );

    expect(saveFidesCookie).not.toHaveBeenCalled();
  });
});
