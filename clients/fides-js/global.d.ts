declare module globalThis {
  /**
   * Wrapper for console.log that only logs if debug mode is enabled
   * while also preserving the stack trace.
   */
  let fidesDebugger: (...args: unknown[]) => void;
}

interface Window {
  /**
   * IAB TCF CMP API. Present when a TCF stub or full CMP is loaded on the page.
   * See: https://github.com/InteractiveAdvertisingBureau/GDPR-Transparency-and-Consent-Framework/blob/master/TCFv2/IAB%20Tech%20Lab%20-%20CMP%20API%20v2.md
   */
  __tcfapi?: (
    command: string,
    version: number,
    callback: (...args: unknown[]) => void,
    parameter?: number | string | boolean,
  ) => void;
}
