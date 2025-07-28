declare module globalThis {
  /** Wrapper for console.log that only logs if debug mode is enabled. */
  let fidesDebugger: (...args: unknown[]) => void;
}
