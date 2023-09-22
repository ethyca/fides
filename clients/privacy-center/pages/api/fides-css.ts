import { NextApiRequest, NextApiResponse } from "next";
import { loadPrivacyCenterEnvironment } from "~/app/server-environment";
import { promises as fsPromises } from "fs";

let cachedFidesCss: string | null = null;
let lastFetched: number | null = null;
const CACHE_DURATION = 3600 * 1000; // Cache for 1 hour

async function loadDefaultFidesCss(): Promise<string> {
  const fidesCssBuffer = await fsPromises.readFile("public/lib/fides.css");
  return fidesCssBuffer.toString();
}

async function refreshFidesCss(): Promise<string> {
  try {
    const environment = await loadPrivacyCenterEnvironment();
    const fidesUrl =
      environment.settings.SERVER_SIDE_FIDES_API_URL ||
      environment.settings.FIDES_API_URL;
    const response = await fetch(`${fidesUrl}/plus/custom-asset/fides_css`);
    const data = await response.text();

    if (!response.ok || !data) {
      throw new Error();
    }

    return data;
  } catch (error) {
    console.warn("Failed to fetch custom fides.css. Using default fides.css.");
    return loadDefaultFidesCss();
  }
}

/**
 * @swagger
 * /fides.css:
 *   get:
 *     description: Returns the custom "fides.css" file. If not available, the default "fides.css" is returned. The response is cached for an hour.
 *     parameters:
 *       - in: query
 *         name: refresh
 *         description: Forces a refresh of the cached CSS.
 *         required: false
 *         schema:
 *           type: boolean
 *     responses:
 *       200:
 *         description: Successfully retrieved "fides.css".
 *         content:
 *           text/css:
 *             schema:
 *               type: string
 */
export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  const currentTime = Date.now();
  const shouldRefresh = "refresh" in req.query;

  // If fides.css isn't cached, the cache has expired, or the refresh parameter is present, refresh fides.css
  if (
    !cachedFidesCss ||
    (lastFetched && currentTime - lastFetched > CACHE_DURATION) ||
    shouldRefresh
  ) {
    try {
      cachedFidesCss = await refreshFidesCss();
      lastFetched = currentTime;
    } catch (error) {
      // Return cached fides.css even if it's stale
      console.error("Error refreshing fides.css:", error);
    }
  }

  res.setHeader("Content-Type", "text/css");
  res.send(cachedFidesCss);
}
