"use server";

/**
 * Root Layout component that wraps the application content.
 *
 * This layout outputs the basic HTML structure and stores the app's config, styles, etc in the Providers component.
 * The layout is shared through the navigation, keeping the app's state and avoiding having to re-fetch data from the server.
 *
 * @param {ReactNode} props.children - The children elements to be rendered within the layout.
 * @returns {ReactNode} The rendered layout component.
 */

import "./ui/global.scss";

import { ReactNode } from "react";

import Providers from "~/components/Providers";

const Layout = async ({ children }: { children: ReactNode }) => {
  return (
    <html lang="en">
      <body>
        <Providers version={process.env.version || "unknown"}>
          {children}
        </Providers>
      </body>
    </html>
  );
};

export default Layout;
