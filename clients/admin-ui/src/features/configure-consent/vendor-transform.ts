import { CONSENT_USE_OPTIONS } from "~/features/configure-consent/constants";
import { Cookies, SystemResponse } from "~/types/api";

export interface CookieBySystem {
  id: SystemResponse["fides_key"];
  name: SystemResponse["name"];
  dataUse?: string;
  cookie?: Cookies;
}

export const transformSystemsToCookies = (
  systems: SystemResponse[],
): CookieBySystem[] => {
  const cookiesList: CookieBySystem[] = [];
  systems.forEach((system) => {
    let addedCookie = false;
    const cookiesWithDataUse = system.privacy_declarations.map((dec) => ({
      cookies: dec.cookies,
      dataUse: dec.data_use,
    }));

    if (cookiesWithDataUse.length) {
      cookiesWithDataUse.forEach((cookieWithDataUse) => {
        const { dataUse, cookies } = cookieWithDataUse;
        cookies?.forEach((cookie) => {
          addedCookie = true;
          cookiesList.push({
            cookie,
            name: system.name,
            id: system.fides_key,
            dataUse,
          });
        });
      });
    }
    // If there were no cookies, we still want to add the system by itself
    // to the table
    if (!addedCookie) {
      cookiesList.push({ name: system.name, id: system.fides_key });
    }
  });
  return cookiesList;
};

export const dataUseIsConsentUse = (dataUse: string) =>
  CONSENT_USE_OPTIONS.some((opt) => opt.value === dataUse.split(".")[0]);
