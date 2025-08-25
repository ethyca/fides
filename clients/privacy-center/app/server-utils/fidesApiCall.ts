import { addCommonHeaders } from "~/common/CommonHeaders";

import loadEnvironmentVariables from "./loadEnvironmentVariables";
import { createLogger } from "./logger";

/**
 * Makes an authenticated API call to the Fides backend
 */
export const makeAuthenticatedFidesApiCall = async <T = any>({
  endpoint,
  method = "GET",
  body,
  token,
}: {
  endpoint: string;
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: any;
  token?: string | null;
}): Promise<{ data: T | null; error: string | null; status: number }> => {
  const log = createLogger();
  const settings = loadEnvironmentVariables();

  // Use server-side URL if available, otherwise fall back to client URL
  const baseUrl = settings.SERVER_SIDE_FIDES_API_URL || settings.FIDES_API_URL;
  const apiToken = token || settings.FIDES_API_TOKEN;

  if (!apiToken) {
    log.warn("No API token provided for authenticated request");
    return {
      data: null,
      error: "No API token available for authenticated request",
      status: 401,
    };
  }

  const url = `${baseUrl}/${endpoint.replace(/^\//, "")}`;
  const headers = new Headers();
  addCommonHeaders(headers, apiToken);

  try {
    log.debug(`Making authenticated API call: ${method} ${url}`);

    const requestOptions: RequestInit = {
      method,
      headers,
    };

    if (body && method !== "GET") {
      if (body instanceof FormData) {
        headers.delete("Content-Type"); // Let browser set multipart boundary
        requestOptions.body = body;
      } else {
        requestOptions.body = JSON.stringify(body);
      }
    }

    const response = await fetch(url, requestOptions);

    let data = null;
    const contentType = response.headers.get("content-type");

    if (contentType && contentType.includes("application/json")) {
      try {
        data = await response.json();
      } catch (e) {
        log.warn("Failed to parse JSON response", e);
      }
    } else {
      const text = await response.text();
      if (text) {
        data = text;
      }
    }

    if (!response.ok) {
      const errorMessage =
        data?.detail || data?.message || `HTTP ${response.status}`;
      log.error(`API call failed: ${errorMessage}`, {
        url,
        status: response.status,
      });
      return {
        data: null,
        error: errorMessage,
        status: response.status,
      };
    }

    log.debug(`API call successful: ${method} ${url}`);
    return {
      data,
      error: null,
      status: response.status,
    };
  } catch (error) {
    log.error(`API call error: ${error}`, { url });
    return {
      data: null,
      error: error instanceof Error ? error.message : "Unknown error occurred",
      status: 500,
    };
  }
};

export default makeAuthenticatedFidesApiCall;
