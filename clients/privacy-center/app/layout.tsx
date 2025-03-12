"use server";

/**
 * Root Layout component that wraps the application content.
 *
 * This layout outputs the basic HTML structure and stores the app's config, styles, etc in the Providers component.
 * The layout is shared through the navigation, keeping the app's state and avoiding having to re-fetch data from the server.
 *
 * @param {ReactElement} props.children - The children elements to be rendered within the layout.
 * @returns {ReactElement} The rendered layout component.
 */

import "./ui/global.scss";

import { ReactElement } from "react";
import Providers from "~/components/Providers";

const Layout = async ({ children }: { children: ReactElement }) => {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
};

export default Layout;
