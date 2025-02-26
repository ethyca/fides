declare global {
  namespace Meta {
    type DataProcessingOption = "LDU";

    /**
     * Facebook doesn't document the many types of arguments this function accepts,
     * they just provides some examples, mainly of the 'track' action.
     *
     * Consent and Limited Data Use have their own examples:
     *  - https://developers.facebook.com/docs/meta-pixel/implementation/gdpr
     *  - https://developers.facebook.com/docs/meta-pixel/implementation/ccpa
     *  - https://developers.facebook.com/docs/marketing-apis/data-processing-options/
     */
    type FBQMethod = {
      (
        method: "dataProcessingOptions",
        options: Array<DataProcessingOption>,
        country?: 0 | 1,
        state?: 0 | 1000,
      ): void;
      (method: "consent", consent: "revoke" | "grant"): void;
      (method: "init", pixelId: string): void;
      (method: string, ...args: any[]): void;
    };

    type FBQObj = {
      loaded: boolean;
      version: string;
      queue: any[];

      callMethod?: FBQMethod;
      push: (...args: Parameters<FBQMethod>) => void;
    };

    type FBQ = FBQMethod & FBQObj;
  }

  interface Window {
    fbq?: Meta.FBQ;
    _fbq?: Meta.FBQ;
  }
}

/**
 * Facebook handles the possibility of the API script being loaded after attempts to call
 * `fbq(args)` by shimming `window.fbq` with a function that just enqueues the args to be called
 * later.
 */
const getFbq = (): Meta.FBQ => {
  if (window.fbq) {
    return window.fbq;
  }

  const shim: Meta.FBQObj = {
    queue: [],
    loaded: true,
    version: "2.0",

    push(...args) {
      const fbq = window.fbq!;
      if (fbq.callMethod) {
        fbq.callMethod(...args);
      } else {
        fbq.queue.push(args);
      }
    },
  };

  window.fbq = Object.assign(shim.push, shim);

  // eslint-disable-next-line no-underscore-dangle
  window._fbq = window.fbq;

  return window.fbq;
};

type MetaOptions = {
  consent: boolean | undefined;
  dataUse: boolean | undefined;
};

/**
 * Call Fides.meta to configure Meta Pixel tracking.
 *
 * DEFER: Update this integration to support async Fides events
 *
 * @example
 * Fides.meta({
 *   consent: Fides.consent.data_sales,
 *   dataUse: Fides.consent.data_sales,
 * })
 */
export const meta = (options: MetaOptions) => {
  const fbq = getFbq();

  fbq("consent", options.consent ? "grant" : "revoke");

  if (options.dataUse) {
    fbq("dataProcessingOptions", []);
  } else {
    // The integer arguments translate to "treat this user as if they are in California" which will
    // limit the use of their data.
    fbq("dataProcessingOptions", ["LDU"], 1, 1000);
  }
};
