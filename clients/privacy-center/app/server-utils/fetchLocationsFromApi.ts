"use server";

import { addCommonHeaders } from "~/common/CommonHeaders";
import { LocationRegulationResponse } from "~/types/api";

import { getFidesApiUrl } from "../server-environment";
import { createLogger } from "./logger";

const fetchLocationsFromApi =
  async (): Promise<LocationRegulationResponse | null> => {
    const log = createLogger();
    const headers = new Headers();
    addCommonHeaders(headers);

    try {
      const url = `${getFidesApiUrl()}/plus/locations`;
      log.debug(`Fetching locations from API: ${url}`);

      const response = await fetch(url, {
        method: "GET",
        headers,
      });
      if (response.ok) {
        return await response.json();
      }
      log.debug(
        `Failed to fetch locations from API: ${response.status} ${response.statusText}`,
      );
    } catch (e) {
      log.debug(`Error fetching locations from API: ${e}`);
    }
    return null;
  };

export default fetchLocationsFromApi;
