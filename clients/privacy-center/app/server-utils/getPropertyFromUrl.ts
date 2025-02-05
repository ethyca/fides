import { addCommonHeaders } from "~/common/CommonHeaders";
import { Property } from "~/types/api";

const getPropertyFromUrl = async ({
  fidesApiUrl,
  customPropertyPath,
  location,
}: {
  fidesApiUrl: string;
  customPropertyPath: string;
  location?: string;
}) => {
  const headers = new Headers();
  addCommonHeaders(headers);

  let result: Property | null = null;
  try {
    const searchParams = new URLSearchParams({
      path: `/${customPropertyPath}`,
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
export default getPropertyFromUrl;
