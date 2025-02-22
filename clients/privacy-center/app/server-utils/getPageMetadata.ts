"use server";

import { Metadata } from "next";

import getPrivacyCenterEnvironmentCached from "./getPrivacyCenterEnvironment";

const getPageMetadata = async (): Promise<Metadata> => {
  const { config } = await getPrivacyCenterEnvironmentCached();

  return {
    title: "Privacy Center",
    description: "Privacy Center",
    icons: {
      icon: config?.favicon_path || "/favicon.ico",
    },
  };
};
export default getPageMetadata;
