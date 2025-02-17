import { addCommonHeaders } from "~/common/CommonHeaders";
import { Property } from "~/types/api";

const fetchPropetyFromApi = async ({
  fidesApiUrl,
  path,
  location,
}: {
  fidesApiUrl: string;
  path: string;
  location?: string | null;
}) => {
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
    fidesDebugger(`Fetching property from API: ${url}`);

    const response = await fetch(url, {
      method: "GET",
      headers,
    });
    if (response.ok) {
      result = await response.json();
    }
  } catch (e) {
    fidesDebugger(`Request to fetch property failed`, e);
  }

  return result;
};
export default fetchPropetyFromApi;
