import { Flex } from "@fidesui/react";
import Head from "next/head";
import * as React from "react";
import { ReactNode } from "react";

import Header from "~/features/common/Header";

type HomeLayoutProps = {
  children: ReactNode;
  title: string;
};

const HomeLayout: React.FC<HomeLayoutProps> = ({ children, title }) => (
  <Flex data-testid={title} direction="column" height="100%">
    <Head>
      <title>Fides Admin UI - {title}</title>
      <meta name="description" content="Privacy Engineering Platform" />
      <link rel="icon" href="/favicon.ico" />
    </Head>
    <Flex height="100%">
      <Flex flexGrow={1} flexDirection="column">
        <Header />
        <Flex as="main" flexDirection="column" gap={10}>
          {children}
        </Flex>
      </Flex>
    </Flex>
  </Flex>
);

export default HomeLayout;
