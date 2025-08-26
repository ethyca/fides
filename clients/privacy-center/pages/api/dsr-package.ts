import type { NextApiRequest, NextApiResponse } from "next";

import loadEnvironmentVariables from "~/app/server-utils/loadEnvironmentVariables";
import validator from "validator";
import { createRequestLogger } from "~/app/server-utils/requestLogger";
import { addCommonHeaders } from "~/common/CommonHeaders";

/**
 * Validates if a string is a valid pri_uuid format (pri_ followed by UUID v4)
 * This function helps prevent SSRF attacks by ensuring only valid UUIDs are processed.
 * @param requestId - The string to validate
 * @returns true if valid pri_uuid format, false otherwise
 */
function isValidRequestId(requestId: string): boolean {
  if (!requestId.startsWith("pri_")) {
    return false;
  }
  const uuidPart = requestId.substring(4); // Remove "pri_" prefix
  return validator.isUUID(uuidPart, 4);
}

/**
 * @swagger
 * /dsr-package:
 *   get:
 *     description: Redirects user to DSR package download URL from the Fides API. Includes security measures to prevent SSRF attacks.
 *     parameters:
 *       - in: query
 *         name: request_id
 *         required: true
 *         description: Privacy request ID in pri_uuid format (e.g., pri_123e4567-e89b-12d3-a456-426614174000). Must start with 'pri_' followed by a valid UUID v4.
 *         schema:
 *           type: string
 *           pattern: '^pri_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
 *     responses:
 *       302:
 *         description: Redirect to the DSR package download URL
 *       400:
 *         description: Bad request - missing or invalid request_id parameter
 *       404:
 *         description: DSR package not found
 *       500:
 *         description: Internal server error
 */
export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse,
) {
  const log = createRequestLogger(req);

  if (req.method !== "GET") {
    res.setHeader("Allow", ["GET"]);
    return res.status(405).send(`Method ${req.method} Not Allowed`);
  }

  try {
    const settings = loadEnvironmentVariables();
    const { request_id: requestIdRaw } = req.query;

    // Extract and validate requestId parameter
    const requestId = Array.isArray(requestIdRaw) ? requestIdRaw[0] : requestIdRaw;

    // Validate that requestId parameter is provided
    if (!requestId) {
      log.warn("DSR package request missing required requestId parameter");
      return res
        .status(400)
        .send("Bad Request: requestId parameter is required");
    }

    // Validate that requestId is a valid pri_uuid to prevent SSRF attacks
    if (typeof requestId !== "string" || !isValidRequestId(requestId)) {
      log.warn("DSR package request with invalid requestId format", { requestId });
      return res
        .status(400)
        .send("Bad Request: requestId must be a valid pri_uuid format");
    }

    // Encode the UUID for safe URL construction
    const encodedRequestId = encodeURIComponent(requestId);

    // Optional: Log if encoding changed the value (shouldn't happen with valid UUIDs)
    if (encodedRequestId !== requestId) {
      log.warn("RequestId was modified during encoding", {
        original: requestId,
        encoded: encodedRequestId
      });
    }

    // Use server-side URL if available, otherwise fall back to client URL
    const baseUrl =
      settings.SERVER_SIDE_FIDES_API_URL || settings.FIDES_API_URL;

    // Build the URL with encoded UUID for safe path parameter
    const url = `${baseUrl}/privacy-request/${encodedRequestId}/access-package`;

    log.debug(`Fetching DSR package link from: ${url}`);

    // Prepare headers for public API call (no authentication)
    const headers = new Headers();
    addCommonHeaders(headers); // No token = public endpoint

    const response = await fetch(url, {
      method: "GET",
      headers,
    });

    let data = null;
    const contentType = response.headers.get("content-type");

    if (contentType && contentType.includes("application/json")) {
      try {
        data = await response.json();
      } catch (e) {
        log.warn("Failed to parse JSON response", e);
      }
    }

    if (!response.ok) {
      const errorMessage =
        data?.detail || data?.message || `HTTP ${response.status}`;
      log.error(`Failed to fetch DSR package link: ${errorMessage}`, {
        url,
        status: response.status,
      });

      // Return appropriate error status with HTML response
      return res
        .status(response.status)
        .send(`Error ${response.status}: ${errorMessage}`);
    }

    // Check if this is a redirect response
    if (response.status === 302 || response.status === 301) {
      const redirectUrl = response.headers.get("location");
      if (redirectUrl) {
        log.info(`Redirecting user to DSR package download URL: ${redirectUrl}`);
        return res.redirect(302, redirectUrl);
      } else {
        log.error("Redirect response missing location header");
        return res.status(500).send("Internal Server Error: Invalid redirect response");
      }
    }

    // If not a redirect, check for JSON response with download_url
    if (data?.download_url) {
      log.info(`Redirecting user to DSR package download URL: ${data.download_url}`);
      return res.redirect(302, data.download_url);
    }

    log.error("Invalid response from Fides API: neither redirect nor download_url found");
    return res
      .status(500)
      .send("Internal Server Error: Invalid response from backend API");
  } catch (error) {
    log.error("Unexpected error in dsr-package endpoint:", error);
    return res
      .status(500)
      .send("Internal Server Error: An unexpected error occurred");
  }
}
