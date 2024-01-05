import { Box, Flex } from "@fidesui/react";
import Head from "next/head";
import * as React from "react";
import { ReactNode } from "react";

import Header from "~/features/common/Header";
import MainSideNav from "~/features/common/nav/v2/MainSideNav";

type HomeLayoutProps = {
  children: ReactNode;
  title: string;
};

const HomeLayout: React.FC<HomeLayoutProps> = ({ children, title }) => (
  <Flex data-testid={title} direction="column">
    <Head>
      <title>Fides Admin UI - {title}</title>
      <meta name="description" content="Privacy Engineering Platform" />
      <link rel="icon" href="/favicon.ico" />
    </Head>
    <Flex>
      <MainSideNav />
      <Flex flexGrow={1} flexDirection="column" gap={10}>
        <Header />
        <Box as="main">{children}</Box>
      </Flex>
    </Flex>
  </Flex>
);

export default HomeLayout;
