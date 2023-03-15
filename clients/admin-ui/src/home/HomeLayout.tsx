import { Flex } from "@fidesui/react";
import Head from "next/head";
import * as React from "react";
import { ReactNode } from "react";

import Header from "~/features/common/Header";
import { NavTopBar } from "~/features/common/nav/v2/NavTopBar";
import NotificationBanner from "~/features/common/NotificationBanner";

type HomeLayoutProps = {
  children: ReactNode;
  title: string;
};

const HomeLayout: React.FC<HomeLayoutProps> = ({ children, title }) => (
  <Flex data-testid={title} direction="column" height="100vh">
    <Head>
      <title>Fides Admin UI - {title}</title>
      <meta name="description" content="" />
      <link rel="icon" href="/favicon.ico" />
    </Head>
    <Header />
    {/* TODO: remove this in a future release (see https://github.com/ethyca/fides/issues/2844) */}
    <NotificationBanner />
    <NavTopBar />
    <Flex as="main" flexDirection="column" gap="40px" height="100%">
      {children}
    </Flex>
  </Flex>
);

export default HomeLayout;
