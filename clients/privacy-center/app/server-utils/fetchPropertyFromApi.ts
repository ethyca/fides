import { addCommonHeaders } from "~/common/CommonHeaders";
import { Property } from "~/types/api";

import { createLogger } from "./loggerContext";

const fetchPropertyFromApi = async ({
  fidesApiUrl,
  path,
  location,
}: {
  fidesApiUrl: string;
  path: string;
  location?: string | null;
}) => {
  const log = createLogger();
  const headers = new Headers();
  addCommonHeaders(headers);

  let result: Property | null = null;
  try {
    // Endpoint params are passed as query params using URLSearchParams
    const searchParams = new URLSearchParams({
      path,
    });
    if (location) {
      searchParams.set("location", location);
    }

    const url = `${fidesApiUrl}/plus/property?${searchParams}`;
    log.debug(`Fetching property from API: ${url}`);

    const response = await fetch(url, {
      method: "GET",
      headers,
    });
    if (response.ok) {
      result = await response.json();
    }
  } catch (e) {
    log.debug(`Request to fetch property failed`, e);
  }

  log.debug(`Fetched property id: ${result?.id}`);
  return result;
};
export default fetchPropertyFromApi;
