import type { NextApiRequest, NextApiResponse } from "next";

import loadEnvironmentVariables from "~/app/server-utils/loadEnvironmentVariables";
import { createRequestLogger } from "~/app/server-utils/requestLogger";
import { addCommonHeaders } from "~/common/CommonHeaders";

interface DSRPackageResponse {
  download_url: string;
  expires_at?: string;
}

/**
 * @swagger
 * /dsr-package:
 *   get:
 *     description: Redirects user to DSR package download URL from the Fides API
 *     parameters:
 *       - in: query
 *         name: request_id
 *         required: false
 *         description: Optional privacy request ID to get package for specific request
 *         schema:
 *           type: string
 *       - in: query
 *         name: email
 *         required: false
 *         description: Optional email to filter packages
 *         schema:
 *           type: string
 *     responses:
 *       302:
 *         description: Redirect to the DSR package download URL
 *       400:
 *         description: Bad request - invalid parameters or missing required params
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
    const { request_id, email } = req.query;

    // Validate that at least one parameter is provided
    if (!request_id && !email) {
      log.warn("DSR package request missing required parameters");
      return res
        .status(400)
        .send("Bad Request: Either request_id or email parameter is required");
    }

    // Use server-side URL if available, otherwise fall back to client URL
    const baseUrl =
      settings.SERVER_SIDE_FIDES_API_URL || settings.FIDES_API_URL;

    // Build query parameters
    const searchParams = new URLSearchParams();
    if (request_id && typeof request_id === "string") {
      searchParams.set("request_id", request_id);
    }
    if (email && typeof email === "string") {
      searchParams.set("email", email);
    }

    const url = `${baseUrl}/dsr-package-link?${searchParams.toString()}`;

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

    log.info(`Successfully fetched DSR package link`);

    // Validate response has required fields
    if (!data?.download_url) {
      log.error("Invalid response from Fides API: missing download_url");
      return res
        .status(500)
        .send("Internal Server Error: Invalid response from backend API");
    }

    // Redirect to the download URL
    log.info(`Redirecting user to DSR package download URL`);
    return res.redirect(302, data.download_url);
  } catch (error) {
    log.error("Unexpected error in dsr-package endpoint:", error);
    return res
      .status(500)
      .send("Internal Server Error: An unexpected error occurred");
  }
}
