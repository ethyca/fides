import { promises as fsPromises } from "fs";
import type { NextApiRequest, NextApiResponse } from "next";
import { CacheControl, stringify } from "cache-control-parser";

import { LOCATION_HEADERS } from "~/common/geolocation";

// one hour, how long the client should cache fides.js for
const GPP_JS_MAX_AGE_SECONDS = 60 * 60;

/**
 * @swagger
 * /gpp.js:
 *   get:
 *     description: TODO
 *     responses:
 *       200:
 *         description: Customized "gpp.js" script extension
 *         content:
 *           application/javascript:
 *             schema:
 *               type: string
 *             example: |
 *               (function(){
 *                 // gpp.js extension bundle...
 *               )();
 */
export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  const gppJsFile = "public/lib/gpp-ext.js";

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
    .setHeader("Cache-Control", stringify(cacheHeaders))
    .setHeader("Vary", LOCATION_HEADERS)
    .send(gppJs);
}
