import { Flex } from "fidesui";
import Head from "next/head";
import React, { ReactNode } from "react";

import BrandLink from "~/components/BrandLink";
import Logo from "~/components/Logo";
import { useConfig } from "~/features/common/config.slice";
import { useSettings } from "~/features/common/settings.slice";
import { useStyles } from "~/features/common/styles.slice";

const Layout = ({ children }: { children: ReactNode }) => {
  const config = useConfig();
  const styles = useStyles();
  const { SHOW_BRAND_LINK } = useSettings();
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
          <Logo src={config.logo_path ?? ""} href={config.logo_url ?? ""} />
        </Flex>
      </header>
      <div>
        {children}
        {SHOW_BRAND_LINK && (
          <BrandLink
            position="absolute"
            bottom={16}
            right={6}
            href="https://fid.es/powered"
          />
        )}
      </div>
    </>
  );
};

export default Layout;
