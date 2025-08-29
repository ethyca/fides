import type { NextApiRequest, NextApiResponse } from "next";
import validator from "validator";

import loadEnvironmentVariables from "~/app/server-utils/loadEnvironmentVariables";
import { createRequestLogger } from "~/app/server-utils/requestLogger";
import { addCommonHeaders } from "~/common/CommonHeaders";

const REQUEST_ID_HEADER = "x-request-id";

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
 * /api/privacy-request/{id}/access-package:
 *   get:
 *     description: Redirects user to DSR package download URL from the Fides API. Includes security measures to prevent SSRF attacks and requires a valid download token.
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         description: Privacy request ID in pri_uuid format (e.g., pri_123e4567-e89b-12d3-a456-426614174000). Must start with 'pri_' followed by a valid UUID v4.
 *         schema:
 *           type: string
 *           pattern: '^pri_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
 *       - in: query
 *         name: token
 *         required: true
 *         description: Download token required for security. This token must be valid and grant access to the specified privacy request.
 *         schema:
 *           type: string
 *     responses:
 *       302:
 *         description: Redirect to the DSR package download URL
 *       400:
 *         description: Bad request - invalid request ID format or missing token
 *       401:
 *         description: Unauthorized - invalid or missing download token
 *       403:
 *         description: Forbidden - token does not grant access to this privacy request
 *       404:
 *         description: DSR package not found
 *       500:
 *         description: Internal server error
 */
export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse,
) {
  // Ensure we have a request ID header for consistent logging
  if (!req.headers[REQUEST_ID_HEADER]) {
    // eslint-disable-next-line no-param-reassign
    req.headers[REQUEST_ID_HEADER] =
      `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  const log = createRequestLogger(req);

  // Set request ID header in response for client correlation
  res.setHeader(REQUEST_ID_HEADER, req.headers[REQUEST_ID_HEADER]);

  if (req.method !== "GET") {
    res.setHeader("Allow", ["GET"]);
    return res.status(405).send(`Method ${req.method} Not Allowed`);
  }

  // Declare variables outside try block for access in catch block
  let url: string | undefined;
  let requestId: string | undefined;
  let token: string | undefined;

  try {
    const settings = loadEnvironmentVariables();
    const { id: requestIdRaw, token: tokenRaw } = req.query;

    // Extract and validate requestId parameter
    requestId = Array.isArray(requestIdRaw)
      ? requestIdRaw[0]
      : requestIdRaw;

    // Extract and validate token parameter
    token = Array.isArray(tokenRaw) ? tokenRaw[0] : tokenRaw;

    // Validate that requestId parameter is provided
    if (!requestId) {
      log.warn("DSR package request missing required requestId parameter");
      return res
        .status(400)
        .send("Bad Request: requestId parameter is required");
    }

    // Validate that token parameter is provided
    if (!token) {
      log.warn("DSR package request missing required token parameter");
      return res.status(400).send("Bad Request: token parameter is required");
    }

    // Validate that requestId is a valid pri_uuid to prevent SSRF attacks
    if (typeof requestId !== "string" || !isValidRequestId(requestId)) {
      log.warn("DSR package request with invalid requestId format", {
        requestId,
      });
      return res
        .status(400)
        .send("Bad Request: requestId must be a valid pri_uuid format");
    }

    // Validate that token is a string
    if (typeof token !== "string") {
      log.warn("DSR package request with invalid token format", {
        token,
      });
      return res.status(400).send("Bad Request: token must be a valid string");
    }

    // Encode the UUID for safe URL construction
    const encodedRequestId = encodeURIComponent(requestId);

    // Optional: Log if encoding changed the value (shouldn't happen with valid UUIDs)
    if (encodedRequestId !== requestId) {
      log.warn("RequestId was modified during encoding", {
        original: requestId,
        encoded: encodedRequestId,
      });
    }

    // Use server-side URL if available, otherwise fall back to client URL
    const baseUrl =
      settings.SERVER_SIDE_FIDES_API_URL || settings.FIDES_API_URL;

    // Build the URL with encoded UUID for safe path parameter
    url = `${baseUrl}/privacy-request/${encodedRequestId}/access-package?token=${encodeURIComponent(token)}`;

    log.info(`🚀 Calling Fides API endpoint:`, {
      baseUrl,
      endpoint: `/privacy-request/${encodedRequestId}/access-package`,
      fullUrl: url,
      requestId: requestId,
      hasToken: !!token,
      tokenLength: token?.length || 0,
    });

    log.debug(`Fetching DSR package link from: ${url}`);

    // Prepare headers for public API call (no authentication)
    const headers = new Headers();
    addCommonHeaders(headers); // No token = public endpoint

    log.debug(`Making request to backend API with headers:`, {
      url,
      method: "GET",
      headers: Object.fromEntries(headers.entries()),
    });

    log.info(`🔍 About to make fetch request to: ${url}`);

    let response: Response;
    try {
      response = await fetch(url, {
        method: "GET",
        headers,
      });

      log.info(`📡 Fides API response received:`, {
        status: response.status,
        statusText: response.statusText,
        url: url,
        responseHeaders: Object.fromEntries(response.headers.entries()),
      });
    } catch (fetchError) {
      // Check if this is a connection refused error
      const isConnectionRefused = fetchError instanceof Error &&
        fetchError.cause &&
        typeof fetchError.cause === 'object' &&
        'code' in fetchError.cause &&
        fetchError.cause.code === 'ECONNREFUSED';

      if (isConnectionRefused) {
        log.error(`❌ Fides API connection refused - service may not be running:`, {
          url,
          error: 'Connection refused (ECONNREFUSED)',
          suggestion: 'Check if Fides API service is running on port 8080',
          baseUrl,
        });
      } else {
        log.error(`❌ Fetch request failed:`, {
          url,
          error: fetchError instanceof Error ? fetchError.message : String(fetchError),
          errorStack: fetchError instanceof Error ? fetchError.stack : undefined,
          errorType: fetchError?.constructor?.name || typeof fetchError,
          fullError: fetchError,
        });
      }
      throw fetchError; // Re-throw to be caught by outer catch block
    }

    let data = null;
    const contentType = response.headers.get("content-type");

    // Capture response data - use arrayBuffer for binary data, text for JSON
    let responseData: ArrayBuffer | string;
    let isBinary = false;

    if (contentType && contentType.includes("application/json")) {
      // For JSON responses, use text
      try {
        responseData = await response.text();
      } catch (e) {
        responseData = "";
        log.warn("Failed to read response body as text", e);
      }
    } else {
      // For binary responses (like ZIP files), use arrayBuffer
      try {
        responseData = await response.arrayBuffer();
        isBinary = true;
      } catch (e) {
        responseData = new ArrayBuffer(0);
        log.warn("Failed to read response body as arrayBuffer", e);
      }
    }

    // Check if this is a redirect response FIRST (before checking response.ok)
    if (response.status === 302 || response.status === 301) {
      const redirectUrl = response.headers.get("location");
      log.debug(`Processing redirect response:`, {
        status: response.status,
        locationHeader: redirectUrl,
        allHeaders: Object.fromEntries(response.headers.entries()),
      });

      if (redirectUrl) {
        log.info(
          `Redirecting user to DSR package download URL: ${redirectUrl}`,
        );
        return res.redirect(302, redirectUrl);
      }
      log.error("Redirect response missing location header", {
        status: response.status,
        headers: Object.fromEntries(response.headers.entries()),
      });
      return res
        .status(500)
        .send("Internal Server Error: Invalid redirect response");
    }

    // Check if the backend returned the actual file content instead of a redirect
    if (
      response.ok &&
      isBinary &&
      responseData instanceof ArrayBuffer &&
      responseData.byteLength > 0
    ) {
      log.info(
        `Backend returned binary file content directly, serving file to user`,
      );

      // Set appropriate headers for file download
      res.setHeader("Content-Type", contentType || "application/octet-stream");
      res.setHeader("Content-Length", responseData.byteLength.toString());
      res.setHeader(
        "Content-Disposition",
        `attachment; filename="privacy-request-${requestId}.zip"`,
      );

      // Return the binary data
      return res.status(200).send(Buffer.from(responseData));
    }

    // Handle JSON responses
    if (
      contentType &&
      contentType.includes("application/json") &&
      !isBinary &&
      typeof responseData === "string"
    ) {
      try {
        data = JSON.parse(responseData);
        log.debug(`Successfully parsed JSON response:`, {
          dataKeys: Object.keys(data),
          hasDownloadUrl: !!data?.download_url,
          downloadUrl: data?.download_url,
        });
      } catch (e) {
        log.warn("Failed to parse JSON response", e);
        log.debug(`Response text that failed to parse:`, {
          responseText: responseData,
        });
      }
    } else if (!isBinary && typeof responseData === "string") {
      log.debug(`Non-JSON text response received:`, {
        contentType,
        responseText: responseData,
      });
    }

    // If not a redirect, check for JSON response with download_url
    if (data?.download_url) {
      log.info(
        `Redirecting user to DSR package download URL: ${data.download_url}`,
      );
      return res.redirect(302, data.download_url);
    }

    // Now check if the response is not ok (this will catch actual errors, not redirects)
    if (!response.ok) {
      const errorMessage =
        data?.detail || data?.message || `HTTP ${response.status}`;
      log.error(`Failed to fetch DSR package link: ${errorMessage}`, {
        url,
        status: response.status,
        statusText: response.statusText,
        responseData: data,
        responseHeaders: Object.fromEntries(response.headers.entries()),
        responseText: responseData,
      });

      // Return appropriate error status with HTML response
      return res
        .status(response.status)
        .send(`Error ${response.status}: ${errorMessage}`);
    }

    // Enhanced logging for the invalid response case
    log.error(
      "Invalid response from Fides API: neither redirect nor download_url found",
      {
        responseStatus: response.status,
        responseStatusText: response.statusText,
        contentType,
        hasData: !!data,
        dataKeys: data ? Object.keys(data) : null,
        data,
        headers: Object.fromEntries(response.headers.entries()),
        url,
      },
    );

    return res
      .status(500)
      .send("Internal Server Error: Invalid response from backend API");
  } catch (error) {
    log.error("Unexpected error in dsr-package endpoint:", {
      error: error instanceof Error ? error.message : String(error),
      errorStack: error instanceof Error ? error.stack : undefined,
      errorType: error?.constructor?.name || typeof error,
      fullError: error,
      url: url || 'unknown',
      requestId: requestId || 'unknown',
      hasToken: !!token,
    });
    return res
      .status(500)
      .send("Internal Server Error: An unexpected error occurred");
  }
}
