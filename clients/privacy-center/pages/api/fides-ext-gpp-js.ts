/**
 * Hosted GPP extension. We use this instead of the `public/` directory
 * because next.js doesn't allow specifying cache headers for statically hosted files
 * https://nextjs.org/docs/pages/api-reference/next-config-js/headers#cache-control
 */

import { CacheControl, stringify } from "cache-control-parser";
import { promises as fsPromises } from "fs";
import type { NextApiRequest, NextApiResponse } from "next";

import { LOCATION_HEADERS } from "~/common/geolocation";

// one hour, how long the client should cache gpp-ext.js for
const GPP_JS_MAX_AGE_SECONDS = 60 * 60;
const GPP_JS_STALE_WHILE_REVALIDATE_SECONDS = 24 * GPP_JS_MAX_AGE_SECONDS;

// File path for the GPP extension bundle
const FIDES_GPP_JS_PATH = "public/lib/fides-ext-gpp.js";

// In-memory cache for the GPP extension bundle to avoid repeated file I/O
let cachedGppJs: string = "";
let gppBundleLoaded: boolean = false;

/**
 * Load the GPP extension bundle into memory to avoid repeated file I/O.
 * This is called on the first request and caches the bundle for the lifetime
 * of the server process.
 */
async function loadGppBundle(): Promise<void> {
  if (gppBundleLoaded) {
    return;
  }

  try {
    const gppJsBuffer = await fsPromises.readFile(FIDES_GPP_JS_PATH);
    cachedGppJs = gppJsBuffer.toString();
    gppBundleLoaded = true;
  } catch (error) {
    gppBundleLoaded = false;
    throw new Error(`Failed to load GPP extension bundle: ${error}`);
  }
}

/**
 * @swagger
 * /fides-ext-gpp.js:
 *   get:
 *     description: Returns the "fides-ext-gpp.js" bundle for dynamic loading
 *     responses:
 *       200:
 *         description: a "fides-ext-gpp.js" script extension
 *         content:
 *           application/javascript:
 *             schema:
 *               type: string
 *             example: |
 *               (function(){
 *                 // fides-ext-gpp.js extension bundle...
 *               )();
 */
export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse,
) {
  // Load bundle into memory cache on first request to avoid file I/O
  await loadGppBundle();

  const gppJs: string = cachedGppJs;
  if (!gppJs || gppJs === "") {
    throw new Error("Unable to load latest gpp-ext.js script from server!");
  }

  // Instruct any caches to store this response, since these bundles do not change often
  const cacheHeaders: CacheControl = {
    "max-age": GPP_JS_MAX_AGE_SECONDS,
    "stale-while-revalidate": GPP_JS_STALE_WHILE_REVALIDATE_SECONDS,
    public: true,
  };

  // Send the bundled script, ready to be loaded directly into a page!
  res
    .status(200)
    .setHeader("Content-Type", "application/javascript")
    // Allow CORS since this is a static file we do not need to lock down
    .setHeader("Access-Control-Allow-Origin", "*")
    .setHeader("Cache-Control", stringify(cacheHeaders))
    .setHeader("Vary", LOCATION_HEADERS)
    .send(gppJs);
}
