import { Box, Flex } from "@fidesui/react";
import Head from "next/head";
import { useRouter } from "next/router";
import React from "react";

import { useFeatures } from "~/features/common/features";
import Header from "~/features/common/Header";
import { NavSideBar } from "~/features/common/nav/v2/NavSideBar";
import { NavTopBar } from "~/features/common/nav/v2/NavTopBar";
import {
  useGetActiveMessagingProviderQuery,
  useGetActiveStorageQuery,
} from "~/features/privacy-requests/privacy-requests.slice";

import ConfigurationNotificationBanner from "../privacy-requests/configuration/ConfigurationNotificationBanner";
import NotificationBanner from "./NotificationBanner";

const Layout = ({
  children,
  title,
}: {
  children: React.ReactNode;
  title: string;
}) => {
  const features = useFeatures();
  const router = useRouter();
  const isValidNotificationRoute =
    router.pathname === "/privacy-requests" ||
    router.pathname === "/datastore-connection";
  const skip = !(
    features.flags.privacyRequestsConfiguration && isValidNotificationRoute
  );

  const { data: activeMessagingProvider } = useGetActiveMessagingProviderQuery(
    undefined,
    { skip }
  );

  const { data: activeStorage } = useGetActiveStorageQuery(undefined, {
    skip,
  });

  const showConfigurationBanner =
    features.flags.privacyRequestsConfiguration &&
    (!activeMessagingProvider || !activeStorage) &&
    isValidNotificationRoute;

  return (
    <Flex
      data-testid={title}
      direction="column"
      minWidth="container.md"
      height="100vh"
    >
      <Head>
        <title>Fides Admin UI - {title}</title>
        <meta name="description" content="Privacy Engineering Platform" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <Header />
      {/* TODO: remove this in a future release (see https://github.com/ethyca/fides/issues/2844) */}
      <NotificationBanner />
      <NavTopBar />
      <Flex as="main" px={9} py={10} gap="40px" height="100%" overflow="auto">
        <Box flex={0} flexShrink={0}>
          <NavSideBar />
        </Box>
        <Flex direction="column" flex={1} minWidth={0}>
          {showConfigurationBanner ? <ConfigurationNotificationBanner /> : null}
          {children}
        </Flex>
      </Flex>
    </Flex>
  );
};

export default Layout;
