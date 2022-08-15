import { Box } from "@fidesui/react";
import Head from "next/head";
import React from "react";

import NavBar from "./NavBar";

const Layout = ({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) => (
  <div>
    <Head>
      <title>Fides Admin UI - {title}</title>
      <meta name="description" content="Generated from FidesUI template" />
      <link rel="icon" href="/favicon.ico" />
    </Head>
    <NavBar />
    <main>
      <Box px={9} py={10}>
        {children}
      </Box>
    </main>
  </div>
);

export default Layout;
