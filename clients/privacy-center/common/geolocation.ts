import type { NextApiRequest } from "next";
import { UserGeolocation } from "fides-js";

// Regex to validate an ISO-3166 location string, which must:
// 1) Start with a 2-3 character country code (e.g. "US")
// 2) Optionally end with a 1-3 character region code (e.g. "CA")
// 3) Separated by a dash (e.g. "US-CA")
const VALID_ISO_3166_LOCATION_REGEX = /^\w{2,3}(-\w{1,3})?$/;

// Regex to validate a standalone ISO-3166-2 region code, which must be a 1-3
// character code (e.g. "CA")
const VALID_ISO_3166_2_REGION_REGEX = /^\w{1,3}?$/;

// Constants for the supported CloudFront geolocation headers
// (see https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/adding-cloudfront-headers.html#cloudfront-headers-viewer-location)
const CLOUDFRONT_HEADER_COUNTRY = "cloudfront-viewer-country";
const CLOUDFRONT_HEADER_REGION = "cloudfront-viewer-country-region";
export const LOCATION_HEADERS = [
  CLOUDFRONT_HEADER_COUNTRY,
  CLOUDFRONT_HEADER_REGION,
];

/**
 * Lookup the "geolocation" (ie country and region) for the given request by looking for either:
 * 1) An explicit "geolocation" query param (e.g. https://privacy.example.com/some/path?geolocation=US-CA)
 * 2) Supported geolocation headers (e.g. "Cloudfront-Viewer-Country: US")
 * 3) A geolocation API URL to infer location based on IP
 *
 * If none of these are found, return a null geolocation.
 *
 */
export const lookupGeolocation = async (
  req: NextApiRequest
): Promise<UserGeolocation | null> => {
  // Check for a provided "geolocation" query param
  const { geolocation: geolocationQuery } = req.query;
  if (
    typeof geolocationQuery === "string" &&
    VALID_ISO_3166_LOCATION_REGEX.test(geolocationQuery)
  ) {
    const [country, region] = geolocationQuery.split("-");
    return {
      location: geolocationQuery,
      country,
      region,
    };
  }

  // Check for CloudFront viewer location headers
  if (typeof req.headers[CLOUDFRONT_HEADER_COUNTRY] === "string") {
    let geolocation;
    let region;
    const country = req.headers[CLOUDFRONT_HEADER_COUNTRY].split(",")[0];
    geolocation = country;
    if (typeof req.headers[CLOUDFRONT_HEADER_REGION] === "string") {
      [region] = req.headers[CLOUDFRONT_HEADER_REGION].split(",");
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
  return null;
};
