declare module globalThis {
  /**
   * Wrapper for console.log that only logs if debug mode is enabled
   * while also preserving the stack trace.
   */
  let fidesDebugger: (...args: unknown[]) => void;
}
