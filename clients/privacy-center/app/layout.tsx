"use server";

import "./ui/global.scss";

import { ReactElement } from "react";

// import getPrivacyCenterEnvironmentCached from "./server-utils/getPrivacyCenterEnvironment";

// export async function generateMetadata() {
//   const { config } = await getPrivacyCenterEnvironmentCached();

//   return {
//     title: "Privacy Center",
//     description: "Privacy Center",
//     icons: {
//       icon: config?.favicon_path || "/favicon.ico",
//     },
//   };
// }

const Layout = async ({ children }: { children: ReactElement }) => {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
};

export default Layout;
