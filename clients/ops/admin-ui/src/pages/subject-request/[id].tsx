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
import { useRouter } from "next/router";
import SubjectRequest from "subject-request/SubjectRequest";

import { INDEX_ROUTE } from "../../constants";
import ProtectedRoute from "../../features/auth/ProtectedRoute";
import Head from "../../features/common/Head";
import NavBar from "../../features/common/NavBar";
import { useGetAllPrivacyRequestsQuery } from "../../features/privacy-requests";

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
      <Text>404 no subject request found</Text>
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
      <div>
        <Head />

        <NavBar />

        <main>
          <Box px={9} py={10}>
            <Heading fontSize="2xl" fontWeight="semibold">
              Subject Request
              <Box mt={2} mb={9}>
                <Breadcrumb fontWeight="medium" fontSize="sm">
                  <BreadcrumbItem>
                    <BreadcrumbLink href={INDEX_ROUTE}>
                      Subject Request
                    </BreadcrumbLink>
                  </BreadcrumbItem>

                  <BreadcrumbItem>
                    <BreadcrumbLink href="#">View Details</BreadcrumbLink>
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
