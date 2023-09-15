import { Flex } from "@fidesui/react";
import React from "react";
import Head from "next/head";
import Logo from "~/components/Logo";

import { useConfig } from "~/features/common/config.slice";
import { useStyles } from "~/features/common/styles.slice";

interface LayoutProps {}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const config = useConfig();
  const styles = useStyles();
  return (
    <>
      <Head>
        <title>Privacy Center</title>
        <meta name="description" content="Privacy Center" />
        <link rel="icon" href={config.favicon_path || "/favicon.ico"} />
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
          <Logo src={config.logo_path} href={config.logo_url} />
        </Flex>
      </header>
      <div>{children}</div>
    </>
  );
};

export default Layout;
