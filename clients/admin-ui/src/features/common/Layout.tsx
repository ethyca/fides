import { Box } from "@fidesui/react";
import Head from "next/head";
import React from "react";

import Header from "./Header";
import NavBar from "./nav/NavBar";

const Layout = ({
  children,
  noPadding,
  title,
}: {
  children: React.ReactNode;
  noPadding?: boolean;
  title: string;
}) => (
  <div>
    <Head>
      <title>Fides Admin UI - {title}</title>
      <meta name="description" content="Generated from FidesUI template" />
      <link rel="icon" href="/favicon.ico" />
    </Head>
    <Header />
    <NavBar />
    <main>
      <Box px={noPadding ? 0 : 9} py={noPadding ? 0 : 10}>
        {children}
      </Box>
    </main>
  </div>
);

export default Layout;
