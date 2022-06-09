import {
  Box,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  Heading,
  Spinner,
  Text,
} from '@fidesui/react';
import type { NextPage } from 'next';
import Head from 'next/head';
import { useRouter } from 'next/router';
import React from 'react';

import ProtectedRoute from '../../features/auth/ProtectedRoute';
import NavBar from '../../features/common/NavBar';
import { useGetAllPrivacyRequestsQuery } from '../../features/privacy-requests';
import SubjectRequest from '../../features/subject-request/SubjectRequest';

const useSubjectRequestDetails = () => {
  const router = useRouter();
  const { id = '' } = router.query;
  const { data, isLoading, isUninitialized } = useGetAllPrivacyRequestsQuery(
    {
      id: Array.isArray(id) ? id[0] : id,
      verbose: true,
    },
    {
      skip: id === '',
    }
  );

  return { data, isLoading, isUninitialized };
};

const SubjectRequestDetails: NextPage = () => {
  const { data, isLoading, isUninitialized } = useSubjectRequestDetails();
  let body =
    !data || data?.items.length === 0 ? (
      <Text>404 no subject request found</Text>
    ) : (
      <SubjectRequest subjectRequest={data?.items[0]!} />
    );

  if (isLoading || isUninitialized) {
    body = <Spinner />;
  }

  return (
    <ProtectedRoute>
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
    </ProtectedRoute>
  );
};

export default SubjectRequestDetails;
