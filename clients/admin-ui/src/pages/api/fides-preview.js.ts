import fs from "fs";
import type { NextApiRequest, NextApiResponse } from "next";
import path from "path";

export default async function handler(_: NextApiRequest, res: NextApiResponse) {
  try {
    const standardPath = path.join(process.cwd(), "public", "lib", "fides.js");
    const tcfPath = path.join(process.cwd(), "public", "lib", "fides-tcf.js");

    const standardContent = fs.readFileSync(standardPath, "utf-8");
    const tcfContent = fs.readFileSync(tcfPath, "utf-8");

    // Create a wrapper that manages execution lifecycle
    const wrapperScript = `
      (function() {
        // Store the script contents but don't execute them
        const scripts = {
          standard: ${JSON.stringify(standardContent)},
          tcf: ${JSON.stringify(tcfContent)}
        };

        // Track current state
        let currentMode = null;
        let currentScript = null;

        // Cleanup function to remove previous execution
        function cleanup() {
          if (currentScript) {
            // Remove the script from DOM to ensure complete cleanup
            currentScript.remove();
            currentScript = null;
            window.Fides = null;
          }
          currentMode = null;
        }

        // Global control method
        window.FidesPreview = function(mode = 'standard') {
          if (currentMode === mode) {
            return; // Already in this mode
          }

          // Clean up previous execution
          cleanup();

          // Create and execute new script
          currentScript = document.createElement('script');
          currentScript.textContent = scripts[mode];
          currentMode = mode;

          // Execute the new script
          document.head.appendChild(currentScript);
        };

        // Expose cleanup function directly
        window.FidesPreview.cleanup = cleanup;
      })();
    `;

    res.setHeader("Content-Type", "application/javascript");
    res.status(200).send(wrapperScript);
  } catch (error) {
    // eslint-disable-next-line no-console
    console.error("Error serving Fides preview script:", error);
    res.status(500).json({ error: "Failed to serve Fides preview script" });
  }
}
