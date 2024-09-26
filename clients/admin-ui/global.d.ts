declare module globalThis {
  // needs to be in global scope of Admin UI for when we import fides-js components which contain fidesDebugger
  let fidesDebugger: (...args: unknown[]) => void;
}
