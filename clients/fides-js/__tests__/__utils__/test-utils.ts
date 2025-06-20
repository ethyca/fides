import {
  FidesCookie,
  FidesGlobal,
  PrivacyExperience,
} from "../../src/lib/consent-types";
import mockExperienceJSON from "../__fixtures__/mock_experience.json";

const mockExperience: Partial<PrivacyExperience> = mockExperienceJSON as any;

/**
 * Creates a mock FidesGlobal object for testing purposes
 * @param overrides - Properties to override in the mock object
 * @returns A mock FidesGlobal object
 */
export const createMockFides = (overrides = {}): FidesGlobal => {
  const mockCookie: FidesCookie = {
    consent: {},
    identity: {},
    fides_meta: {},
    tcf_consent: {},
  };

  return {
    consent: {},
    experience: mockExperience,
    geolocation: { country: "US" },
    locale: "en",
    options: {
      debug: true,
      fidesApiUrl: "https://example.com/api",
      fidesDisableSaveApi: false,
    },
    fides_meta: {},
    identity: {},
    tcf_consent: {},
    saved_consent: {},
    config: { propertyId: "prop1" },
    initialized: true,
    cookie: mockCookie,
    encodeNoticeConsentString: jest.fn().mockReturnValue("encoded-nc-string"),
    decodeNoticeConsentString: jest.fn().mockReturnValue({ analytics: true }),
    ...overrides,
  } as unknown as FidesGlobal;
};

/**
 * Creates a mock FidesCookie object for testing purposes
 * @param overrides - Properties to override in the mock cookie
 * @returns A mock FidesCookie object
 */
export const createMockCookie = (overrides = {}): FidesCookie => ({
  consent: {},
  identity: {},
  fides_meta: {},
  tcf_consent: {},
  ...overrides,
});

/**
 * Sets up common global mocks for fides-js tests
 */
export const setupGlobalMocks = (): void => {
  if (!window.fidesDebugger) {
    window.fidesDebugger = jest.fn();
  }
};
