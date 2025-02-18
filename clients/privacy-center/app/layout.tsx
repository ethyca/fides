"use server";

/**
 * Root Layout component that wraps the application content.
 *
 * This layout outputs the basic HTML structure. In Next.js, it doesn't have access to query parameters
 * or dynamic route props here, so the PageLayout component is used instead for rendering the logo or custom styles.
 *
 * @param {ReactElement} props.children - The children elements to be rendered within the layout.
 * @returns {ReactElement} The rendered layout component.
 */

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
