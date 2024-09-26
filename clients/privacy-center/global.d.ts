declare module globalThis {
  let fidesDebugger: (...args: unknown[]) => void;
  let fidesError: (...args: unknown[]) => void;
}
