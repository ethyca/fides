import { Box, Button, Flex, Heading } from "@fidesui/react";
import type { NextPage } from "next";
import Head from "next/head";
import NextLink from "next/link";
import React from "react";

import Header from "../features/common/Header";
// import Setup from './setup';
import { ArrowDownLineIcon } from "../features/common/Icon";

const Home: NextPage<{ session: { username: string } }> = ({ session }) => (
  <div>
    <Head>
      <title>Fides Admin UI</title>
      <meta name="description" content="Generated from FidesUI template" />
      <link rel="icon" href="/favicon.ico" />
    </Head>

    <Header username={session && session.username} />

    <main>
      {/* NEED TO FLAG BEFORE RELEASE
      Show Setup when the user is an admin and there are zero systems registered in the database */}
      {/* <Setup /> */}

      <Flex
        borderBottom="1px"
        borderTop="1px"
        px={9}
        py={1}
        borderColor="gray.100"
      >
        <Button variant="ghost" mr={4} colorScheme="complimentary">
          Subject Requests
        </Button>
        <Button variant="ghost" disabled mr={4}>
          Datastore Connections
        </Button>
        <Button variant="ghost" disabled mr={4}>
          User Management
        </Button>
        {/* This is a temporary link to the config wizard while it's still in progress */}
        <NextLink href="/config-wizard" passHref>
          <Button variant="ghost" disabled mr={4}>
            Config Wizard
          </Button>
        </NextLink>
        <Button variant="ghost" disabled rightIcon={<ArrowDownLineIcon />}>
          More
        </Button>
      </Flex>
      <Box px={9} py={10}>
        <Heading mb={8} fontSize="2xl" fontWeight="semibold">
          Subject Requests
        </Heading>
      </Box>
    </main>
  </div>
);

// TODO: replace auth https://github.com/ethyca/fidesui/issues/2
// export const getServerSideProps = wrapper.getServerSideProps(
//   (store) => async (context) => {
//     const session = await getSession(context);
//     if (session && typeof session.accessToken !== 'undefined') {
//       await store.dispatch(assignToken(session.accessToken));
//       return { props: { session } };
//     }

//     // TODO: once user login is implemented in fides-ctl, re-enable this to make
//     // sure the home page is login-protected
//     return {
//       //   redirect: {
//       //     destination: '/login',
//       //     permanent: false,
//       //   },
//     };
//   }
// );

export default Home;
