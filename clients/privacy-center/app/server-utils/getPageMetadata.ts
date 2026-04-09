"use server";

import { Metadata } from "next";

import getPrivacyCenterEnvironmentCached from "./getPrivacyCenterEnvironment";

const getPageMetadata = async (): Promise<Metadata> => {
  const { config } = await getPrivacyCenterEnvironmentCached();

  return {
    title: config?.page_title || "Privacy Center",
    description: "Privacy Center",
    icons: {
      icon: config?.favicon_path || "/favicon.ico",
    },
    robots: { index: false },
  };
};
export default getPageMetadata;
