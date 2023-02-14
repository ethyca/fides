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
  <div data-testid={title}>
    <Head>
      <title>Fides Admin UI - {title}</title>
      <meta name="description" content="" />
      <link rel="icon" href="/favicon.ico" />
    </Head>
    <Header />
    <NavTopBar />
    <Flex flexDirection="column" gap="40px" width="100vw">
      {children}
    </Flex>
  </div>
);

export default HomeLayout;
