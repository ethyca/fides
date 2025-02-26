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
  const gppJsFile = "public/lib/fides-ext-gpp.js";

  const gppJsBuffer = await fsPromises.readFile(gppJsFile);
  const gppJs: string = gppJsBuffer.toString();
  if (!gppJs || gppJs === "") {
    throw new Error("Unable to load latest gpp-ext.js script from server!");
  }

  // Instruct any caches to store this response, since these bundles do not change often
  const cacheHeaders: CacheControl = {
    "max-age": GPP_JS_MAX_AGE_SECONDS,
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
