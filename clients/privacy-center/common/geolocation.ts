import { UserGeolocation } from "fides-js";
import type { NextApiRequest } from "next";

/**
 * Regex to validate a [ISO 3166-2](https://en.wikipedia.org/wiki/ISO_3166-2) code:
 * 1. Starts with a 2 letter country code (e.g. "US", "GB") (see [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2))
 * 2. (Optional) Ends with a 1-3 alphanumeric character region code (e.g. "CA", "123", "X") (see [ISO 3166-2](https://en.wikipedia.org/wiki/ISO_3166-2))
 * 3. Country & region codes must be separated by a hyphen (e.g. "US-CA")
 *
 * Fides also supports a special `EEA` geolocation code to denote the European
 * Economic Area; this is not part of ISO 3166-2, but is supported for
 * convenience.
 */
export const VALID_ISO_3166_LOCATION_REGEX =
  /^(?:([a-z]{2})(-[a-z0-9]{1,3})?|(eea))$/i;

// Regex to validate a standalone ISO-3166-2 region code, which must be a 1-3
// alphanumeric character region code (e.g. "CA", "123", "X")
export const VALID_ISO_3166_2_REGION_REGEX = /^[a-z0-9]{1,3}?$/i;

// Constants for the supported CloudFront geolocation headers
// (see https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/adding-cloudfront-headers.html#cloudfront-headers-viewer-location)
export const CLOUDFRONT_HEADER_COUNTRY = "cloudfront-viewer-country";
export const CLOUDFRONT_HEADER_REGION = "cloudfront-viewer-country-region";
export const LOCATION_HEADERS = [
  CLOUDFRONT_HEADER_COUNTRY,
  CLOUDFRONT_HEADER_REGION,
];

/**
 * Lookup the "geolocation" (ie country and region) for the given request by looking for either:
 * 1) An explicit "geolocation" query param (e.g. https://privacy.example.com/some/path?geolocation=US-CA)
 * 2) Supported geolocation headers (e.g. "Cloudfront-Viewer-Country: US")
 *
 * If none of these are found, return a null geolocation.
 *
 */
export const lookupGeolocation = async (
  req: NextApiRequest,
): Promise<UserGeolocation | null> => {
  // Check for a provided "geolocation" query param
  const { geolocation: geolocationQuery } = req.query;
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
