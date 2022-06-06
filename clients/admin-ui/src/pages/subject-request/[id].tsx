import {
  Box,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  Heading,
  Text,
} from '@fidesui/react';
import type { NextPage } from 'next';
import Head from 'next/head';
import { getSession } from 'next-auth/react';
import React from 'react';

import { useAppSelector } from '../../app/hooks';
import { wrapper } from '../../app/store';
import NavBar from '../../features/common/NavBar';
import {
  privacyRequestApi,
  selectPrivacyRequestFilters,
  setRequestId,
  setVerbose,
  useGetAllPrivacyRequestsQuery,
} from '../../features/privacy-requests';
import SubjectRequest from '../../features/subject-request/SubjectRequest';
import { assignToken, setUser } from '../../features/user';

const SubjectRequestDetails: NextPage<{}> = () => {
  const filters = useAppSelector(selectPrivacyRequestFilters);
  const { data } = useGetAllPrivacyRequestsQuery(filters);
  const body =
    data?.items.length === 0 ? (
      <Text>404 no subject request found</Text>
    ) : (
      <SubjectRequest subjectRequest={data?.items[0]!} />
    );

  return (
    <div>
      <Head>
        <title>Fides Admin UI - Subject Request Details</title>
        <meta name='description' content='Subject Request Details' />
        <link rel='icon' href='/favicon.ico' />
      </Head>

      <NavBar />

      <main>
        <Box px={9} py={10}>
          <Heading fontSize='2xl' fontWeight='semibold'>
            Subject Request
            <Box mt={2} mb={9}>
              <Breadcrumb fontWeight='medium' fontSize='sm'>
                <BreadcrumbItem>
                  <BreadcrumbLink href='/'>Subject Request</BreadcrumbLink>
                </BreadcrumbItem>

                <BreadcrumbItem>
                  <BreadcrumbLink href='#'>View Details</BreadcrumbLink>
                </BreadcrumbItem>
              </Breadcrumb>
            </Box>
          </Heading>
          {body}
        </Box>
      </main>
    </div>
  );
};

export default SubjectRequestDetails;

export const getServerSideProps = wrapper.getServerSideProps(
  (store) => async (context) => {
    const session = await getSession(context);
    if (session && typeof session.accessToken !== 'undefined') {
      await store.dispatch(assignToken(session.accessToken));
      await store.dispatch(setUser(session.user));
      await store.dispatch(setRequestId(context.query.id as string));
      await store.dispatch(setVerbose(true));
      const state = store.getState();

      if (context.query.id) {
        const filters = selectPrivacyRequestFilters(state);
        delete filters.status;
        store.dispatch(
          privacyRequestApi.endpoints.getAllPrivacyRequests.initiate(filters)
        );
        await Promise.all(privacyRequestApi.util.getRunningOperationPromises());
      }

      return { props: {} };
    }

    return {
      redirect: {
        destination: '/login',
        permanent: false,
      },
    };
  }
);
