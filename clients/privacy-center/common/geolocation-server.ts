"use server";

import { headers } from "next/headers";
import {
  CLOUDFRONT_HEADER_COUNTRY,
  CLOUDFRONT_HEADER_REGION,
  VALID_ISO_3166_2_REGION_REGEX,
  VALID_ISO_3166_LOCATION_REGEX,
} from "./geolocation";

interface lookupGeolocationServerSideParams {
  searchParams: {
    [key: string]: string;
  };
}

/**
 * Lookup the "geolocation" (ie country and region) for the given request by looking for either:
 * 1) An explicit "geolocation" query param (e.g. https://privacy.example.com/some/path?geolocation=US-CA)
 * 2) Supported geolocation headers (e.g. "Cloudfront-Viewer-Country: US")
 *
 * If none of these are found, return an undefined geolocation.
 *
 */
export const lookupGeolocationServerSide = async ({
  searchParams,
}: lookupGeolocationServerSideParams) => {
  // 1. Check for a provided "geolocation" query param
  const { geolocation: geolocationQuery } = searchParams;
  console.log("searchParams", searchParams);
  if (typeof geolocationQuery === "string") {
    if (!VALID_ISO_3166_LOCATION_REGEX.test(geolocationQuery)) {
      throw new Error(
        `Provided location (${geolocationQuery}) query parameter is not in ISO 3166 format.`,
      );
    }

    const [country, region] = geolocationQuery.split("-");
    return {
      location: geolocationQuery,
      country,
      region,
    };
  }

  // 2. Check for CloudFront viewer location headers
  const headersList = await headers();
  const cdnHeaderCountry = headersList.get(CLOUDFRONT_HEADER_COUNTRY);
  const cdnHeaderRegion = headersList.get(CLOUDFRONT_HEADER_REGION);

  if (typeof cdnHeaderCountry === "string") {
    let geolocation;
    let region;
    const country = cdnHeaderCountry.split(",")[0];
    geolocation = country;
    if (typeof cdnHeaderRegion === "string") {
      [region] = cdnHeaderRegion.split(",");
      // Check if the region header is valid; otherwise discard (it's optional!)
      if (VALID_ISO_3166_2_REGION_REGEX.test(region)) {
        geolocation = `${country}-${region}`;
      } else {
        region = undefined;
      }
    }
    if (VALID_ISO_3166_LOCATION_REGEX.test(geolocation)) {
      return {
        location: geolocation,
        country,
        region,
      };
    }
  }

  return undefined;
};
