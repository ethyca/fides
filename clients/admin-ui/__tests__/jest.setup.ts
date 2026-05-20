import "@testing-library/jest-dom";
import "whatwg-fetch";

import { installMessageChannelMock } from "./utils/message-channel-mock";
import { installResizeObserverMock } from "./utils/resize-observer-mock";

jest.mock(
  "iso-3166",
  () => jest.requireActual("./utils/iso-3166-mock").iso3166Mock,
);

// Workaround for nwsapi 2.2.18 + jsdom: `:has()` selector resolution calls
// `.includes()` on a NodeList, which doesn't exist by default.
if (
  typeof NodeList !== "undefined" &&
  // @ts-expect-error patching missing prototype method
  typeof NodeList.prototype.includes !== "function"
) {
  // @ts-expect-error patching missing prototype method
  NodeList.prototype.includes = Array.prototype.includes;
}

// nwsapi 2.2.18 + jsdom: when antd v6 stylesheets contain `:has()` selectors,
// the resolver crashes inside `getComputedStyle` (called by Chakra's
// color-mode-provider on mount). Wrap `getComputedStyle` so a thrown selector
// returns an empty CSSStyleDeclaration instead of breaking the render.
if (typeof window !== "undefined") {
  const originalGetComputedStyle = window.getComputedStyle.bind(window);
  window.getComputedStyle = ((
    elt: Element,
    pseudoElt?: string | null,
  ): CSSStyleDeclaration => {
    try {
      return originalGetComputedStyle(elt, pseudoElt ?? undefined);
    } catch {
      return {
        getPropertyValue: () => "",
      } as unknown as CSSStyleDeclaration;
    }
  }) as typeof window.getComputedStyle;
}

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

  installResizeObserverMock();
}

installMessageChannelMock();
