export const initializeDebugger = (isDebugMode: boolean) => {
  // Initialize the global fidesDebugger function if it doesn't already exist
  if (typeof window !== "undefined" && !window.fidesDebugger) {
    const debugMarker = "=>";
    window.fidesDebugger = isDebugMode
      ? // eslint-disable-next-line no-console
        (...args) => console.log(`\x1b[33m${debugMarker}\x1b[0m`, ...args)
      : () => {};
    window.fidesError = isDebugMode
      ? // eslint-disable-next-line no-console
        (...args) => console.log(`\x1b[31m${debugMarker}\x1b[0m`, ...args)
      : () => {};
  } else {
    // avoid any errors if window is not defined
    (globalThis as any).fidesDebugger = () => {};
    (globalThis as any).fidesError = () => {};
  }
  // will only log if debug mode is enabled
  fidesDebugger("Fides debugger enabled");
};
