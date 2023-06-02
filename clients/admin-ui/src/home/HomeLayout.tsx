import { Flex } from "@fidesui/react";
import Head from "next/head";
import * as React from "react";
import { ReactNode } from "react";

import Header from "~/features/common/Header";
import { NavTopBar } from "~/features/common/nav/v2/NavTopBar";

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
    <Header />
    <NavTopBar />
    <Flex as="main" flexGrow={1} flexDirection="column" gap={10}>
      {children}
    </Flex>
  </Flex>
);

export default HomeLayout;
