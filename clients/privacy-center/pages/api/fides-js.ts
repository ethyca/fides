/* eslint-disable no-console */
import { promises as fsPromises } from "fs";
import type { NextApiRequest, NextApiResponse } from "next";

import { ConsentOption, FidesConfig } from "fides-js";
import { loadPrivacyCenterEnvironment } from "~/app/server-environment";

/**
 * Server-side API route to generate the customized "fides.js" script
 * based on the current configuration values.
 *
 * TODO: if this actually works, make sure we cache the results aggressively!
 */
export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  // Load the configured consent options (data uses, defaults, etc.) from environment
  const environment = await loadPrivacyCenterEnvironment();
  let options: ConsentOption[] = [];
  if (environment.config?.consent?.page.consentOptions) {
    const configuredOptions = environment.config.consent.page.consentOptions;
    options = configuredOptions.map((option) => ({
      fidesDataUseKey: option.fidesDataUseKey,
      default: option.default,
      cookieKeys: option.cookieKeys,
    }));
  }

  // Create the FidesConfig object that will be used to initialize fides.js
  const fidesConfig: FidesConfig = {
    consent: {
      options,
    },
  };
  const fidesConfigJSON = JSON.stringify(fidesConfig);

  // TODO: need to get a copy of the file during build stage, not load from ../ paths!
  console.log(
    "Bundling generic fides.js & Privacy Center configuration together..."
  );
  const fidesJS = await fsPromises.readFile("../fides-js/dist/fides.js");
  const script = `
  (function () {
    // Include generic fides.js script
    ${fidesJS}

    // Initialize fides.js with custom config
    var fidesConfig = ${fidesConfigJSON};
    window.Fides.init(fidesConfig);
  })();
  `;

  // Send the bundled script, ready to be loaded directly into a page!
  res
    .status(200)
    .setHeader("Content-Type", "application/javascript")
    .send(script);
}
