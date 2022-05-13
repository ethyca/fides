import { Box, Button, Flex, Heading } from '@fidesui/react';
import type { NextPage } from 'next';
import Head from 'next/head';
import { getSession } from 'next-auth/react';
import React from 'react';

import { wrapper } from '../app/store';
import Header from '../features/common/Header';
import { ArrowDownLineIcon } from '../features/common/Icon';
import RequestFilters from '../features/privacy-requests/RequestFilters';
import RequestTable from '../features/privacy-requests/RequestTable';
import { assignToken } from '../features/user/user.slice';

const Home: NextPage<{ session: { username: string } }> = ({ session }) => (
  <div>
    <Head>
      <title>Fides Admin UI</title>
      <meta name="description" content="Generated from FidesUI template" />
      <link rel="icon" href="/favicon.ico" />
    </Head>

    <Header username={session.username} />

    <main>
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
        <Button variant="ghost" disabled rightIcon={<ArrowDownLineIcon />}>
          More
        </Button>
      </Flex>
      <Box px={9} py={10}>
        <Heading mb={8} fontSize="2xl" fontWeight="semibold">
          Subject Requests
        </Heading>
        <RequestFilters />
        <RequestTable />
      </Box>
    </main>
  </div>
);

export const getServerSideProps = wrapper.getServerSideProps(
  (store) => async (context) => {
    const session = await getSession(context);
    if (session && typeof session.accessToken !== 'undefined') {
      await store.dispatch(assignToken(session.accessToken));
      return { props: { session } };
    }

    return {
      redirect: {
        destination: '/login',
        permanent: false,
      },
    };
  }
);

export default Home;
