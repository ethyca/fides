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
    const searchParams = new URLSearchParams({
      path,
    });
    if (location) {
      searchParams.set("location", location);
    }

    console.log("Fetching property with params", searchParams.toString());
    const response = await fetch(
      `${fidesApiUrl}/plus/property?${searchParams}`,
      {
        method: "GET",
        headers,
      },
    );
    if (response.ok) {
      result = await response.json();
    }
  } catch (e) {
    // eslint-disable-next-line no-console
    console.log("Request to find property failed", e);
  }

  return result;
};
export default fetchPropetyFromApi;
