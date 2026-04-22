"use server";

import { addCommonHeaders } from "~/common/CommonHeaders";

import { getFidesApiUrl } from "../server-environment";
import { createLogger } from "./logger";

export interface LocationOption {
  id: string;
  name: string;
}

const fetchLocationsFromApi = async (): Promise<LocationOption[]> => {
  const log = createLogger();
  const headers = new Headers();
  addCommonHeaders(headers);

  try {
    const url = `${getFidesApiUrl()}/plus/privacy-request-metrics/locations`;
    log.debug(`Fetching disclosure locations from API: ${url}`);

    const response = await fetch(url, {
      method: "GET",
      headers,
    });
    if (response.ok) {
      return await response.json();
    }
    log.debug(
      `Failed to fetch disclosure locations: ${response.status} ${response.statusText}`,
    );
  } catch (e) {
    log.debug(`Error fetching disclosure locations: ${e}`);
  }
  return [];
};

export default fetchLocationsFromApi;
