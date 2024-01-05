import { Box, Flex } from "@fidesui/react";
import Head from "next/head";
import { useRouter } from "next/router";
import React from "react";

import { useFeatures } from "~/features/common/features";
import Header from "~/features/common/Header";
import MainSideNav from "~/features/common/nav/v2/MainSideNav";
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

  const showConfigurationBanner =
    features.flags.privacyRequestsConfiguration &&
    (!activeMessagingProvider || !activeStorage) &&
    isValidNotificationRoute;

  return (
    <Flex data-testid={title} direction="column">
      <Head>
        <title>Fides Admin UI - {title}</title>
        <meta name="description" content="Privacy Engineering Platform" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <Flex>
        <MainSideNav />
        <Flex direction="column" flex={1} minWidth={0}>
          <Header />
          <Box as="main" py={6} px={10}>
            {showConfigurationBanner ? (
              <ConfigurationNotificationBanner />
            ) : null}
            {children}
          </Box>
        </Flex>
      </Flex>
    </Flex>
  );
};

export default Layout;
