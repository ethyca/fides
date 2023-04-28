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
import { PRIVACY_EXPERIENCE_ROUTE } from "~/features/common/nav/v2/routes";
import { useGetPrivacyExperienceByIdQuery } from "~/features/privacy-experience/privacy-experience.slice";
import { ComponentType } from "~/types/api";

const PrivacyExperienceDetailPage = () => {
  const router = useRouter();

  let experienceId = "";
  if (router.query.id) {
    experienceId = Array.isArray(router.query.id)
      ? router.query.id[0]
      : router.query.id;
  }

  const { data, isLoading } = useGetPrivacyExperienceByIdQuery(experienceId);

  if (isLoading) {
    return (
      <Layout title="Privacy experience">
        <Center>
          <Spinner />
        </Center>
      </Layout>
    );
  }

  if (!data) {
    return (
      <Layout title="Privacy experience">
        <Text>No privacy experience with id {experienceId} found.</Text>
      </Layout>
    );
  }

  const header =
    data.component === ComponentType.OVERLAY
      ? "Configure your consent overlay"
      : "Configure your privacy center";

  return (
    <Layout title={`Privacy experience ${data.component}`}>
      <Box mb={4}>
        <Heading
          fontSize="2xl"
          fontWeight="semibold"
          mb={2}
          data-testid="header"
        >
          {header}
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
              <NextLink href={PRIVACY_EXPERIENCE_ROUTE}>
                Privacy experience
              </NextLink>
            </BreadcrumbItem>
            <BreadcrumbItem color="complimentary.500">
              <NextLink href="#">{data.name}</NextLink>
            </BreadcrumbItem>
          </Breadcrumb>
        </Box>
      </Box>
      <Box width={{ base: "100%", lg: "70%" }}>
        <Text fontSize="sm" mb={8}>
          Configure the text of your privacy overlay, privacy banner, and the
          text of the buttons which users will click to accept, reject, manage,
          and save their preferences. This privacy overlay contains opt-in
          privacy notices and must be delivered with a banner.
        </Text>
        <Box data-testid="privacy-experience-detail-page">
          Work in progress!
        </Box>
      </Box>
    </Layout>
  );
};

export default PrivacyExperienceDetailPage;
