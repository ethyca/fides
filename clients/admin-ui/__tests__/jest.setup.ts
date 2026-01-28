import "@testing-library/jest-dom";
import "whatwg-fetch";

// eslint-disable-next-line global-require
jest.mock("iso-3166", () => require("./utils/iso-3166-mock").iso3166Mock);

// Mock window.matchMedia for Ant Design components (only in jsdom environment)
if (typeof window !== "undefined") {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: jest.fn().mockImplementation((query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: jest.fn(), // deprecated
      removeListener: jest.fn(), // deprecated
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    })),
  });
}
