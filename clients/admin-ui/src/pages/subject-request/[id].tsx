import {
  Box,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  Center,
  Heading,
  Spinner,
  Text,
} from "@fidesui/react";
import type { NextPage } from "next";
import NextLink from "next/link";
import { useRouter } from "next/router";
import { useGetAllPrivacyRequestsQuery } from "privacy-requests/index";
import React from "react";
import SubjectRequest from "subject-request/SubjectRequest";

import Layout from "~/features/common/Layout";

import { INDEX_ROUTE } from "../../constants";
import ProtectedRoute from "../../features/auth/ProtectedRoute";

const useSubjectRequestDetails = () => {
  const router = useRouter();
  const { id = "" } = router.query;
  const { data, isLoading, isUninitialized } = useGetAllPrivacyRequestsQuery(
    {
      id: Array.isArray(id) ? id[0] : id,
      verbose: true,
    },
    {
      skip: id === "",
    }
  );

  return { data, isLoading, isUninitialized };
};

const SubjectRequestDetails: NextPage = () => {
  const { data, isLoading, isUninitialized } = useSubjectRequestDetails();
  let body =
    !data || data?.items.length === 0 ? (
      <Text>404 no privacy request found</Text>
    ) : (
      <SubjectRequest subjectRequest={data?.items[0]!} />
    );

  if (isLoading || isUninitialized) {
    body = (
      <Center>
        <Spinner />
      </Center>
    );
  }

  return (
    <ProtectedRoute>
      <Layout title="Privacy Request">
        <Heading fontSize="2xl" fontWeight="semibold">
          Privacy Request
          <Box mt={2} mb={9}>
            <Breadcrumb fontWeight="medium" fontSize="sm">
              <BreadcrumbItem>
                <BreadcrumbLink as={NextLink} href={INDEX_ROUTE}>
                  Privacy Request
                </BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbItem>
                <BreadcrumbLink
                  isCurrentPage
                  color="complimentary.500"
                  _hover={{ textDecoration: "none" }}
                >
                  View Details
                </BreadcrumbLink>
              </BreadcrumbItem>
            </Breadcrumb>
          </Box>
        </Heading>
        {body}
      </Layout>
    </ProtectedRoute>
  );
};

export default SubjectRequestDetails;
