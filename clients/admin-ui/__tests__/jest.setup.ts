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

// Wrap `getComputedStyle` for two jsdom limitations:
//   1. jsdom doesn't implement pseudo-element styles, so any `pseudoElt`
//      argument triggers a "Not implemented: window.computedStyle(elt,
//      pseudoElt)" log via its VirtualConsole. @rc-component's scrollbar
//      measurement passes one, so we drop it (pseudo-element styles aren't
//      available in jsdom anyway).
//   2. nwsapi 2.2.18 crashes resolving antd v6's `:has()` selectors, so fall
//      back to an empty CSSStyleDeclaration when the underlying call throws.
if (typeof window !== "undefined") {
  const originalGetComputedStyle = window.getComputedStyle.bind(window);
  window.getComputedStyle = ((elt: Element): CSSStyleDeclaration => {
    try {
      return originalGetComputedStyle(elt);
    } catch {
      return {
        getPropertyValue: () => "",
        length: 0,
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

// Filter console.error output for known noise that doesn't indicate a real bug.
// React passes its warnings as a format string + substitutions (e.g.
// `console.error("An update to %s inside a test...", "BaseSelect")`), so we
// match against the unformatted first argument.
//   - antd List deprecation warning (no drop-in replacement exists yet)
//   - rc-trigger's "same shadow root" warning (jsdom doesn't implement shadow DOM)
//   - `NaN` height from antd-x Sender/Bubble.List measuring DOM that jsdom can't lay out
//   - React `act()` warnings from async updates in antd Select / next/dynamic /
//     rc-trigger that fire after the test assertion and can't be reasonably awaited
const SUPPRESSED_CONSOLE_ERRORS = [
  "[antd: List] The `List` component is deprecated",
  "trigger element and popup element should in same shadow root",
  "`NaN` is an invalid value for the `%s` css style property",
  "An update to %s inside a test was not wrapped in act",
];

/* eslint-disable no-console */
const originalConsoleError = console.error;
console.error = (...args: unknown[]) => {
  const message = String(args[0] ?? "");
  if (SUPPRESSED_CONSOLE_ERRORS.some((pattern) => message.includes(pattern))) {
    return;
  }
  originalConsoleError(...args);
};
/* eslint-enable no-console */
