import { Flex } from "fidesui";
import Head from "next/head";
import * as React from "react";
import { ReactNode } from "react";

type HomeLayoutProps = {
  children: ReactNode;
  title: string;
};

const HomeLayout = ({ children, title }: HomeLayoutProps) => (
  <Flex vertical data-testid={title} style={{ height: "100%" }}>
    <Head>
      <title>Fides Admin UI - {title}</title>
      <meta name="description" content="Privacy Engineering Platform" />
      <link rel="icon" href="/favicon.ico" />
    </Head>
    <Flex vertical gap={40} component="main">
      {children}
    </Flex>
  </Flex>
);

export default HomeLayout;
