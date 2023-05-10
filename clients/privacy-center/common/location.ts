import type { NextApiRequest } from "next";

// DEFER: Import this type from fides-js when it exists!
// (see https://github.com/ethyca/fides/pull/3191)
// import type { UserGeolocation } from "fides-js";
export type UserGeolocation = {
  country?: string; // "US"
  ip?: string; // "192.168.0.1:12345"
  location?: string; // "US-NY"
  region?: string; // "NY"
};

// Regex to validate a location string, which must:
// 1) Start with a 2-3 character country code (e.g. "US")
// 2) Optionally end with a 2-3 character region code (e.g. "CA")
// 3) Separated by a dash (e.g. "US-CA")
const VALID_ISO_3166_LOCATION_REGEX = /^\w{2,3}(-\w{2,3})?$/;

// Constants for the supported CloudFront geolocation headers
// (see https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/adding-cloudfront-headers.html#cloudfront-headers-viewer-location)
const CLOUDFRONT_HEADER_COUNTRY = "cloudfront-viewer-country";
const CLOUDFRONT_HEADER_REGION = "cloudfront-viewer-country-region";
export const LOCATION_HEADERS = [
  CLOUDFRONT_HEADER_COUNTRY,
  CLOUDFRONT_HEADER_REGION,
];

/**
 * Lookup the "location" (ie country and region) for the given request by looking for either:
 * 1) An explicit "location" query param (e.g. https://privacy.example.com/some/path?location=US-CA)
 * 2) Supported geolocation headers (e.g. "Cloudfront-Viewer-Country: US")
 *
 * If neither of these are found, return an undefined location.
 *
 * NOTE: This specifically *does not* include performing a geo-IP lookup... yet!
 */
export const getLocation = (
  req: NextApiRequest
): UserGeolocation | undefined => {
  // DEFER: read headers to determine & return the request's IP address

  // Check for a provided "location" query param
  const { location: locationQuery } = req.query;
  if (
    typeof locationQuery === "string" &&
    VALID_ISO_3166_LOCATION_REGEX.test(locationQuery)
  ) {
    const [country, region] = locationQuery.split("-");
    return {
      location: locationQuery,
      country,
      region,
    };
  }

  // Check for CloudFront viewer location headers
  if (typeof req.headers[CLOUDFRONT_HEADER_COUNTRY] === "string") {
    let location;
    let region;
    const country = req.headers[CLOUDFRONT_HEADER_COUNTRY].split(",")[0];
    location = country;
    if (typeof req.headers[CLOUDFRONT_HEADER_REGION] === "string") {
      [region] = req.headers[CLOUDFRONT_HEADER_REGION].split(",");
      location = `${country}-${region}`;
    }
    if (VALID_ISO_3166_LOCATION_REGEX.test(location)) {
      return {
        location,
        country,
        region,
      };
    }
  }
  return undefined;
};
