/* eslint-disable class-methods-use-this */
/* eslint-disable no-underscore-dangle */
/* eslint-disable max-classes-per-file */
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

  // Ant Design v6 uses ResizeObserver internally for popup positioning and
  // virtual scrolling. jsdom does not implement it.
  if (typeof window.ResizeObserver === "undefined") {
    window.ResizeObserver = jest.fn().mockImplementation(() => ({
      observe: jest.fn(),
      unobserve: jest.fn(),
      disconnect: jest.fn(),
    }));
  }
}

// Ant Design v6's @rc-component/form uses MessageChannel for batching field
// watcher notifications. The jsdom version used by this project doesn't include
// it. Provide a functional stub that routes port1 → port2 messages so that
// Form.useWatch() works correctly in tests.
if (typeof MessageChannel === "undefined") {
  class MockMessagePort {
    onmessage: ((e: { data: unknown }) => void) | null = null;

    _other: MockMessagePort | null = null;

    postMessage(data: unknown) {
      const other = this._other;
      if (other?.onmessage) {
        // Schedule asynchronously to match real MessageChannel behaviour
        Promise.resolve().then(() => other.onmessage?.({ data }));
      }
    }

    start() {}

    close() {}

    addEventListener() {}

    removeEventListener() {}

    dispatchEvent() {
      return true;
    }
  }

  class MockMessageChannel {
    port1: MockMessagePort;

    port2: MockMessagePort;

    constructor() {
      this.port1 = new MockMessagePort();
      this.port2 = new MockMessagePort();
      this.port1._other = this.port2;
      this.port2._other = this.port1;
    }
  }

  // @ts-expect-error -- functional stub for jsdom; matches MessageChannel API surface used by @rc-component/form
  global.MessageChannel = MockMessageChannel;
}
