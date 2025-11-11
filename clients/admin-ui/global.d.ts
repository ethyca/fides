declare module globalThis {
  // needs to be in global scope of Admin UI for when we import fides-js components which contain fidesDebugger
  let fidesDebugger: (...args: unknown[]) => void;
}

interface Window {
  // Cypress is available on window when running in Cypress tests
  Cypress?: any;
  // Redux store is exposed for Cypress testing
  __REDUX_STORE__?: any;
}
