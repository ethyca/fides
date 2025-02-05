"use server";

import "./ui/global.scss";

import Header from "~/components/Header";

import Providers from "./Providers";
import { NextPage } from "next";
import { loadPrivacyCenterEnvironment } from "./server-environment";
import { headers } from "next/headers";
import { lookupGeolocationServerSide } from "~/common/geolocation-server";
import { ReactElement } from "react";

export async function generateMetadata() {
  return {
    title: "Privacy Center",
    description: "Privacy Center",
    // icons: {
    //   icon: config?.favicon_path || "/favicon.ico",
    // },
  };
}

const Layout = async ({ children }: { children: ReactElement }) => {
  const headersList = await headers();

  const searchParams = await getSearchParams();
  const location = await lookupGeolocationServerSide({ searchParams });

  // Load the server-side environment for the session and pass it to the client as props
  const customPropertyPath = headersList.get("customPropertyPath")?.toString();
  const serverEnvironment = await loadPrivacyCenterEnvironment({
    customPropertyPath,
    location: location?.location,
  });

  const { settings, config, property, styles } = serverEnvironment;
  console.log("location", location);

  return (
    <html lang="en">
      <body>
        {styles ? <style suppressHydrationWarning>{styles}</style> : null}
        <Header logoPath={config?.logo_path!} logoUrl={config?.logo_url!} />
        <div>
          <Providers serverEnvironment={serverEnvironment}>
            {children}
          </Providers>
        </div>
      </body>
    </html>
  );
};

/*
  This is a workround for getting query params into the layout,
  middleware.ts sets the query params as headers so we can
  read it here.
  src: https://github.com/vercel/next.js/discussions/54955#discussioncomment-11744585
*/
const getSearchParams = async () => {
  const headerStore = await headers();
  const searchParams = Object.fromEntries(
    new URLSearchParams(headerStore.get("searchParams") || ""),
  );
  return searchParams;
};
export default Layout;
