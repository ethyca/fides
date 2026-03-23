/**
 * Polyfill for ResizeObserver in the jsdom test environment.
 *
 * Ant Design v6 uses ResizeObserver internally for popup positioning and
 * virtual scrolling. jsdom does not implement it, so we provide a no-op mock.
 * Tests that need to assert on resize callbacks can replace this mock per-test.
 */
export function installResizeObserverMock() {
  if (
    typeof window !== "undefined" &&
    typeof window.ResizeObserver === "undefined"
  ) {
    window.ResizeObserver = jest.fn().mockImplementation(() => ({
      observe: jest.fn(),
      unobserve: jest.fn(),
      disconnect: jest.fn(),
    }));
  }
}
