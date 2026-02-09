/**
 * Cleans up URL query parameters while optionally preserving specific params.
 * Useful after OAuth callbacks to remove temporary state/error params.
 *
 * @param preserveParams - Object with param names and values to keep in URL
 */
export const cleanupUrlParams = (
  preserveParams?: Record<string, string>,
): void => {
  const url = new URL(window.location.href);
  const { pathname } = url;

  if (preserveParams && Object.keys(preserveParams).length > 0) {
    const params = new URLSearchParams();
    Object.entries(preserveParams).forEach(([key, value]) => {
      params.set(key, value);
    });
    const newUrl = `${pathname}?${params.toString()}`;
    window.history.replaceState({}, "", newUrl);
  } else {
    window.history.replaceState({}, "", pathname);
  }
};

/**
 * Gets OAuth error message based on error code.
 */
export const getOAuthErrorMessage = (errorCode: string): string => {
  const errorMessages: Record<string, string> = {
    invalid_state:
      "Authorization failed: Invalid state token. Please try again.",
    not_configured: "Authorization failed: Chat provider not configured.",
    token_failed: "Authorization failed: Could not obtain access token.",
    no_token: "Authorization failed: No token received from Slack.",
  };

  return errorMessages[errorCode] ?? "Authorization failed. Please try again.";
};
