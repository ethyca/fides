export const initializeDebugger = (isDebugMode: boolean) => {
  // Initialize the global fidesDebugger function if it doesn't already exist
  if (typeof window !== "undefined" && !window.fidesDebugger) {
    // eslint-disable-next-line no-console
    window.fidesDebugger = isDebugMode ? console.log : () => {};
  } else {
    // avoid any errors if window is not defined
    (globalThis as any).fidesDebugger = () => {};
  }
  // will only log if debug mode is enabled
  fidesDebugger("Fides debugger enabled");
};
