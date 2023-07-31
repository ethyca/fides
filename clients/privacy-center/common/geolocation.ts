import type { NextApiRequest } from "next";
import { getGeolocation, UserGeolocation } from "fides-js";
import {PrivacyCenterClientSettings} from "~/app/server-environment";

// Regex to validate a location string, which must:
// 1) Start with a 2-3 character country code (e.g. "US")
// 2) Optionally end with a 2-3 character region code (e.g. "CA")
// 3) Separated by a dash (e.g. "US-CA")
const VALID_ISO_3166_LOCATION_REGEX = /^\w{2,3}(-\w{2,3})?$/;

// Constants for the supported CloudFront geolocation headers
// (see https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/adding-cloudfront-headers.html#cloudfront-headers-viewer-location)
const CLOUDFRONT_HEADER_COUNTRY = "cloudfront-viewer-country";
const CLOUDFRONT_HEADER_REGION = "cloudfront-viewer-country-region";
const X_FORWARDED_FOR = "X-Forwarded-For";
export const LOCATION_HEADERS = [
  CLOUDFRONT_HEADER_COUNTRY,
  CLOUDFRONT_HEADER_REGION,
  X_FORWARDED_FOR,
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
  req: NextApiRequest,
  settings: PrivacyCenterClientSettings
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
      geolocation = `${country}-${region}`;
    }
    if (VALID_ISO_3166_LOCATION_REGEX.test(geolocation)) {
      return {
        location: geolocation,
        country,
        region,
      };
    }
  }

  if (settings.IS_OVERLAY_ENABLED && settings.IS_PREFETCH_ENABLED) {
    // read headers to determine if we have request's IP address
    if (typeof req.headers[X_FORWARDED_FOR] === "string") {
      const forwarded_ip_info = req.headers[X_FORWARDED_FOR];
      return getGeolocation(
          settings.IS_GEOLOCATION_ENABLED,
          settings.GEOLOCATION_API_URL,
          forwarded_ip_info,
          settings.DEBUG
      );
    }
  }
  return null;
};
