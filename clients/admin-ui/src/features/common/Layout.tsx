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

  const showNotificationBanner =
    features.flags.privacyRequestsConfiguration &&
    (!activeMessagingProvider || !activeStorage) &&
    isValidNotificationRoute;

  return (
    <div data-testid={title}>
      <Head>
        <title>Fides Admin UI - {title}</title>
        <meta name="description" content="Generated from FidesUI template" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <Header />
      <NavTopBar />
      <Flex as="main" px={9} py={10} gap="40px">
        <Box flex={0} flexShrink={0}>
          <NavSideBar />
        </Box>
        <Flex direction="column" flex={1} minWidth={0}>
          {showNotificationBanner ? <ConfigurationNotificationBanner /> : null}
          {children}
        </Flex>
      </Flex>
    </div>
  );
};

export default Layout;
