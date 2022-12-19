import { Box, Flex } from "@fidesui/react";
import Head from "next/head";
import React from "react";

import { useFeatures } from "~/features/common/features.slice";
import Header from "~/features/common/Header";
import NavBar from "~/features/common/nav/NavBar";
import { NavSideBar } from "~/features/common/nav/v2/NavSideBar";
import { NavTopBar } from "~/features/common/nav/v2/NavTopBar";

const Layout = ({
  children,
  title,
}: {
  children: React.ReactNode;
  title: string;
}) => {
  const features = useFeatures();

  return (
    <div data-testid={title}>
      <Head>
        <title>Fides Admin UI - {title}</title>
        <meta name="description" content="Generated from FidesUI template" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <Header />

      {features.navV2 ? (
        <>
          <NavTopBar />
          <Flex as="main" px={9} py={10} gap="40px">
            <Box flex={0} flexShrink={0}>
              <NavSideBar />
            </Box>
            <Flex direction="column" flex={1} minWidth={0}>
              {children}
            </Flex>
          </Flex>
        </>
      ) : (
        <>
          <NavBar />
          <main>
            <Box px={9} py={10}>
              {children}
            </Box>
          </main>
        </>
      )}
    </div>
  );
};

export default Layout;
