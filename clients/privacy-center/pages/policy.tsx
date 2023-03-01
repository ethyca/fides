import React from "react";
import type { NextPage } from "next";
import Head from "next/head";
import { Flex, Stack, Image } from "@fidesui/react";

import { config } from "~/constants";

const PrivacyPolicy: NextPage = () => (
  <div>
    <Head>
      <title>Snackpass Privacy Center - Privacy Policy</title>
      <meta name="description" content="Privacy Center" />
      <link rel="icon" href="/favicon.ico" />
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

    <main data-testid="home">
      <Stack align="center" py={["6", "16"]} px={5} spacing={14}>
        <iframe
          src="https://legal.snackpass.co/snackpass-privacy-policy"
          title="Snackpass Privacy Policy"
        />
      </Stack>
    </main>
  </div>
);

export default PrivacyPolicy;
