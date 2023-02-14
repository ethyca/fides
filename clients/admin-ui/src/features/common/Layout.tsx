import { Box, Flex } from "@fidesui/react";
import Head from "next/head";
import { useRouter } from "next/router";
import React from "react";

import { useFeatures } from "~/features/common/features";
import Header from "~/features/common/Header";
import NavBar from "~/features/common/nav/NavBar";
import { NavSideBar } from "~/features/common/nav/v2/NavSideBar";
import { NavTopBar } from "~/features/common/nav/v2/NavTopBar";
import {
  useGetActiveMessagingProviderQuery,
  useGetActiveStorageQuery,
} from "~/features/privacy-requests/privacy-requests.slice";

import ConfigurationNotificationBanner from "../privacy-requests/configuration/ConfigurationNotificationBanner";

const Layout = ({
  children,
  title,
}: {
  children: React.ReactNode;
  title: string;
}) => {
  const features = useFeatures();
  const router = useRouter();
  const { data: activeMessagingProvider } =
    useGetActiveMessagingProviderQuery();
  const { data: activeStorage } = useGetActiveStorageQuery();
  const showConfigurationNotificationBanner =
    (!activeStorage || !activeMessagingProvider) &&
    features.flags.privacyRequestsConfiguration &&
    (router.pathname === "/privacy-requests" ||
      router.pathname === "/datastore-connection");

  return (
    <div data-testid={title}>
      <Head>
        <title>Fides Admin UI - {title}</title>
        <meta name="description" content="Generated from FidesUI template" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <Header />

      {features.flags.navV2 ? (
        <>
          <NavTopBar />
          <Flex as="main" px={9} py={10} gap="40px">
            <Box flex={0} flexShrink={0}>
              <NavSideBar />
            </Box>
            <Flex direction="column" flex={1} minWidth={0}>
              {showConfigurationNotificationBanner ? (
                <ConfigurationNotificationBanner />
              ) : null}
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
