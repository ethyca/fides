"use server";

import { headers } from "next/headers";

import debugLogServer from "~/app/server-utils/debugLogServer";
import { NextSearchParams } from "~/types/next";

import {
  CLOUDFRONT_HEADER_COUNTRY,
  CLOUDFRONT_HEADER_REGION,
  VALID_ISO_3166_2_REGION_REGEX,
  VALID_ISO_3166_LOCATION_REGEX,
} from "./geolocation";

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
}: {
  searchParams?: NextSearchParams;
} = {}) => {
  // 1. Check for a provided "geolocation" query param
  if (searchParams) {
    const { geolocation: geolocationQuery } = await searchParams;
    if (typeof geolocationQuery === "string") {
      if (!VALID_ISO_3166_LOCATION_REGEX.test(geolocationQuery)) {
        throw new Error(
          `Provided location (${geolocationQuery}) query parameter is not in ISO 3166 format.`,
        );
      }

      const [country, region] = geolocationQuery.split("-");
      const location = geolocationQuery.replace("-", "_");
      debugLogServer(`Using location provided via query param: ${location}`);

      return {
        location,
        country,
        region,
      };
    }
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
      const location = geolocation.replace("-", "_").toLowerCase();
      debugLogServer(`Using location provided by CDN headers: ${location}`);

      return {
        location,
        country,
        region,
      };
    }
  }

  debugLogServer(`Using location: null`);
  return null;
};
