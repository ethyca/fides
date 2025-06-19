"use client";

import { useEffect } from "react";

interface VersionLoggerProps {
  version: string;
}

const VersionLogger = ({ version }: VersionLoggerProps) => {
  useEffect(() => {
    if (version !== "__RELEASE_VERSION__") {
      // eslint-disable-next-line no-console
      console.info(`Privacy Center version: ${version}`);
    }
  }, [version]);

  return null; // This component doesn't render anything
};

export default VersionLogger;
