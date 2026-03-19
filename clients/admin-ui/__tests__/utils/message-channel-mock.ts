/* eslint-disable class-methods-use-this */
/* eslint-disable max-classes-per-file */
/**
 * Polyfill for MessageChannel in the jsdom test environment.
 *
 * Ant Design v6's @rc-component/form uses MessageChannel for batching field
 * watcher notifications (Form.useWatch). The jsdom version used by this
 * project doesn't include it, so we provide a functional stub that correctly
 * routes port1 → port2 messages asynchronously.
 */
export function installMessageChannelMock() {
  if (typeof MessageChannel !== "undefined") {
    return;
  }

  class MockMessagePort {
    onmessage: ((e: { data: unknown }) => void) | null = null;

    private other: MockMessagePort | null = null;

    postMessage = (data: unknown) => {
      const { other } = this;
      if (other?.onmessage) {
        // Schedule asynchronously to match real MessageChannel behaviour
        Promise.resolve().then(() => other.onmessage?.({ data }));
      }
    };

    start = () => {};

    close = () => {};

    addEventListener = () => {};

    removeEventListener = () => {};

    dispatchEvent = () => true;

    link(other: MockMessagePort) {
      this.other = other;
    }
  }

  class MockMessageChannel {
    port1 = new MockMessagePort();

    port2 = new MockMessagePort();

    constructor() {
      this.port1.link(this.port2);
      this.port2.link(this.port1);
    }
  }

  // @ts-expect-error -- functional stub for jsdom; matches MessageChannel API surface used by @rc-component/form
  global.MessageChannel = MockMessageChannel;
}
