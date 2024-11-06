/* eslint-disable jsdoc/no-missing-syntax */
import * as fidesJSPackage from "fides-js/package.json";
import { NextApiRequest, NextApiResponse } from "next";

import * as privacyCenterPackage from "../../package.json";

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  try {
    res.status(200).json({
      core_fides_version: fidesJSPackage.version,
      privacy_center_version: privacyCenterPackage.version,
    });
  } catch (error) {
    res.status(500).json({ error: "failed to get health check" });
  }
}
