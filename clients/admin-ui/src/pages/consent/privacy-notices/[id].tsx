import { PRIVACY_REQUESTS_ROUTE } from "@fidesui/components";
import {
  Box,
  Breadcrumb,
  BreadcrumbItem,
  Center,
  Heading,
  Spinner,
  Text,
} from "@fidesui/react";
import NextLink from "next/link";
import { useRouter } from "next/router";

import Layout from "~/features/common/Layout";
import { PRIVACY_NOTICES_ROUTE } from "~/features/common/nav/v2/routes";
import { useGetPrivacyNoticeByIdQuery } from "~/features/privacy-notices/privacy-notices.slice";
import PrivacyNoticeForm from "~/features/privacy-notices/PrivacyNoticeForm";

const PrivacyNoticeDetailPage = () => {
  const router = useRouter();

  let noticeId = "";
  if (router.query.id) {
    noticeId = Array.isArray(router.query.id)
      ? router.query.id[0]
      : router.query.id;
  }

  const { data, isLoading } = useGetPrivacyNoticeByIdQuery(noticeId);

  if (isLoading) {
    return (
      <Layout title="Privacy notice">
        <Center>
          <Spinner />
        </Center>
      </Layout>
    );
  }

  if (!data) {
    return (
      <Layout title="Privacy notice">
        <Text>No privacy notice with id {noticeId} found.</Text>
      </Layout>
    );
  }

  return (
    <Layout title={`Privacy notice ${data.name}`}>
      <Box mb={4}>
        <Heading
          fontSize="2xl"
          fontWeight="semibold"
          mb={2}
          data-testid="header"
        >
          {data.name}
        </Heading>
        <Box>
          <Breadcrumb
            fontWeight="medium"
            fontSize="sm"
            color="gray.600"
            data-testid="breadcrumbs"
          >
            <BreadcrumbItem>
              <NextLink href={PRIVACY_REQUESTS_ROUTE}>
                Privacy requests
              </NextLink>
            </BreadcrumbItem>
            {/* TODO: Add Consent breadcrumb once the page exists */}
            <BreadcrumbItem>
              <NextLink href={PRIVACY_NOTICES_ROUTE}>Privacy notices</NextLink>
            </BreadcrumbItem>
            <BreadcrumbItem color="complimentary.500">
              <NextLink href="#">{data.name}</NextLink>
            </BreadcrumbItem>
          </Breadcrumb>
        </Box>
      </Box>
      <Box width={{ base: "100%", lg: "50%" }}>
        <Text fontSize="sm" mb={8}>
          Configure your privacy notice including consent mechanism, associated
          data uses and the locations in which this should be displayed to
          users.
        </Text>
        <Box data-testid="privacy-notice-detail-page">
          <PrivacyNoticeForm privacyNotice={data} />
        </Box>
      </Box>
    </Layout>
  );
};

export default PrivacyNoticeDetailPage;
