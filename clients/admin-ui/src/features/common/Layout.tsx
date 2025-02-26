import { Flex, FlexProps } from "fidesui";
import Head from "next/head";
import { useRouter } from "next/router";
import React from "react";

import { useFeatures } from "~/features/common/features";
import {
  useGetActiveMessagingProviderQuery,
  useGetActiveStorageQuery,
} from "~/features/privacy-requests/privacy-requests.slice";

import ConfigurationNotificationBanner from "../privacy-requests/configuration/ConfigurationNotificationBanner";

const Layout = ({
  children,
  title,
  padded = true,
  mainProps,
}: {
  children: React.ReactNode;
  title: string;
  padded?: boolean;
  /**
   * Layouts are generally standardized, so make sure you actually want to use this!
   * Currently only used on the home page and datamap pages
   * which have different padding requirements compared to other pages in the app.
   */
  mainProps?: FlexProps;
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
    { skip },
  );

  const { data: activeStorage } = useGetActiveStorageQuery(undefined, {
    skip,
  });

  const showConfigurationBanner =
    features.flags.privacyRequestsConfiguration &&
    (!activeMessagingProvider || !activeStorage) &&
    isValidNotificationRoute;

  return (
    <Flex data-testid={title} direction="column" h="100vh">
      <Head>
        <title>Fides Admin UI - {title}</title>
        <meta name="description" content="Privacy Engineering Platform" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <Flex
        as="main"
        direction="column"
        py={padded ? 6 : 0}
        px={padded ? 10 : 0}
        h={padded ? "calc(100% - 48px)" : "full"}
        flex={1}
        minWidth={0}
        overflow="auto"
        {...mainProps}
      >
        {showConfigurationBanner ? <ConfigurationNotificationBanner /> : null}
        {children}
      </Flex>
    </Flex>
  );
};

export default Layout;
