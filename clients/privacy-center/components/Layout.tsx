import { Flex, Image } from "@fidesui/react";
import React from "react";
import Head from "next/head";

import { useConfig } from "~/features/common/config.slice";

// TODO: get styles from store
interface LayoutProps {
  styles?: string;
}

const Layout: React.FC<LayoutProps> = ({ children, styles }) => {
  const config = useConfig();
  return (
    <>
      <Head>
        <title>Privacy Center</title>
        <meta name="description" content="Privacy Center" />
        <link rel="icon" href="/favicon.ico" />
        {styles ? <style>{styles}</style> : null}
      </Head>
      <header>
        <Flex
          bg="gray.100"
          minHeight={14}
          p={1}
          width="100%"
          justifyContent="center"
          alignItems="center"
        >
          <Image
            src={config.logo_path}
            margin="8px"
            height="68px"
            alt="Logo"
            data-testid="logo"
          />
        </Flex>
      </header>
      <div>{children}</div>
    </>
  );
};

export default Layout;
