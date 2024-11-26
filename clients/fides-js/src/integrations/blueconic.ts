import { MARKETING_CONSENT_KEYS } from "../lib/consent-constants";

declare global {
  interface Window {
    blueConicClient?: {
      profile?: {
        getProfile: () => {
          setConsentedObjectives: (objectives: string[]) => void;
          setRefusedObjectives: (objectives: string[]) => void;
        };
        updateProfile: () => void;
      };
      event?: {
        subscribe: any;
      };
    };
  }
}

// https://support.blueconic.com/hc/en-us/articles/202605221-JavaScript-front-end-API
const blueConicLoaded = () =>
  typeof window.blueConicClient !== "undefined" &&
  typeof window.blueConicClient.event !== "undefined" &&
  typeof window.blueConicClient.event.subscribe !== "undefined";

const configureObjectives = () => {
  if (!blueConicLoaded() || !window.blueConicClient?.profile) {
    return;
  }

  const profile = window.blueConicClient?.profile?.getProfile();

  const { consent } = window.Fides;
  const hasConsentFlags =
    consent !== undefined && Object.entries(consent).length > 0;
  const optedIn = MARKETING_CONSENT_KEYS.some((key) => consent[key]);
  if (!hasConsentFlags || optedIn) {
    profile.setConsentedObjectives([
      "iab_purpose_1",
      "iab_purpose_2",
      "iab_purpose_3",
      "iab_purpose_4",
    ]);
    profile.setRefusedObjectives([]);
  } else {
    profile.setConsentedObjectives(["iab_purpose_1"]);
    profile.setRefusedObjectives([
      "iab_purpose_2",
      "iab_purpose_3",
      "iab_purpose_4",
    ]);
  }

  window.blueConicClient.profile.updateProfile();
};

export const blueconic = (
  { approach }: { approach: "onetrust" } = { approach: "onetrust" },
) => {
  if (approach !== "onetrust") {
    throw new Error("Unsupported approach");
  }

  window.addEventListener("FidesInitialized", configureObjectives);
  window.addEventListener("FidesUpdated", configureObjectives);
  window.addEventListener("onBlueConicLoaded", configureObjectives);

  configureObjectives();
};
