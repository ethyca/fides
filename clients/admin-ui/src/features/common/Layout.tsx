import { Box } from "@fidesui/react";
import NavBar from "common/NavBar";
import Head from "next/head";
import React from "react";

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
