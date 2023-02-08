declare global {
  interface Navigator {
    globalPrivacyControl?: boolean;
  }
}

export type ConsentContext = {
  globalPrivacyControl?: boolean;
};

export const getConsentContext = (): ConsentContext => {
  if (typeof window === "undefined") {
    return {};
  }

  return {
    globalPrivacyControl: window.navigator.globalPrivacyControl,
  };
};
