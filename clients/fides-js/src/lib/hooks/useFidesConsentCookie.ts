import { useEffect, useState } from "preact/hooks";

import { FidesCookie, FidesInitOptions } from "../consent-types";
import { getFidesConsentCookie } from "../cookie";

/**
 * Hook to load and manage the Fides consent cookie with proper cleanup
 * to prevent race conditions when the cookie suffix changes.
 */
export const useFidesConsentCookie = (
  fidesCookieSuffix: FidesInitOptions["fidesCookieSuffix"],
): FidesCookie | undefined => {
  const [parsedCookie, setParsedCookie] = useState<FidesCookie | undefined>(
    undefined,
  );

  useEffect(() => {
    let isMounted = true;
    const loadCookie = async () => {
      const cookieData = await getFidesConsentCookie(fidesCookieSuffix);
      if (isMounted) {
        setParsedCookie(cookieData);
      }
    };
    loadCookie();
    return () => {
      isMounted = false;
    };
  }, [fidesCookieSuffix]);

  return parsedCookie;
};
