import { NextApiRequest, NextApiResponse } from "next";
import { loadPrivacyCenterEnvironment } from "~/app/server-environment";

let cachedCss: string | null = null;
let lastFetched: number | null = null;
const CACHE_DURATION = 3600 * 1000; // Cache for 1 hour

async function fetchFidesCss(): Promise<string> {
  const environment = await loadPrivacyCenterEnvironment();
  const fidesUrl =
    environment.settings.SERVER_SIDE_FIDES_API_URL ||
    environment.settings.FIDES_API_URL;
  const response = await fetch(`${fidesUrl}/plus/custom-asset/fides_css`);
  if (!response.ok) {
    throw new Error("Failed to fetch CSS");
  }
  const data = await response.text();
  return data;
}

export default async (req: NextApiRequest, res: NextApiResponse) => {
  const currentTime = Date.now();

  const shouldRefresh = "refresh" in req.query;

  // If no CSS is cached, the cache has expired, or the refresh parameter is present, fetch new CSS
  if (
    !cachedCss ||
    (lastFetched && currentTime - lastFetched > CACHE_DURATION) ||
    shouldRefresh
  ) {
    try {
      cachedCss = await fetchFidesCss();
      lastFetched = currentTime;
    } catch (error) {
      // Handle fetch error (e.g., return cached CSS even if it's stale)
      console.error("Error fetching Fides CSS:", error);
    }
  }

  res.setHeader("Content-Type", "text/css");
  res.send(cachedCss || "");
};
