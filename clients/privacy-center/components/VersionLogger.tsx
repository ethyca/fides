"use client";

import { useEffect } from "react";

interface VersionLoggerProps {
  version: string;
}

const VersionLogger = ({ version }: VersionLoggerProps) => {
  useEffect(() => {
    /**
     * The version is set in the next.config.js file and replaced
     * by the using versioneer during the docker build process.
     *
     * If the version is not set, it means we are running locally
     * so we don't want to log the version.
     */
    if (version && version !== "unknown") {
      // eslint-disable-next-line no-console
      console.info(`Fides Privacy Center version: ${version}`);
    }
  }, [version]);

  return null; // This component doesn't render anything
};

export default VersionLogger;
