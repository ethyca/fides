import { Box, Center, Heading, Spinner, Text } from "@fidesui/react";
import { useRouter } from "next/router";

import Layout from "~/features/common/Layout";
import BackButton from "~/features/common/nav/v2/BackButton";
import { PRIVACY_NOTICES_ROUTE } from "~/features/common/nav/v2/routes";
import {
  useGetAvailableNoticeTranslationsQuery,
  useGetPrivacyNoticeByIdQuery,
} from "~/features/privacy-notices/privacy-notices.slice";
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
  const { data: availableTranslations } =
    useGetAvailableNoticeTranslationsQuery(noticeId);

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
      <BackButton backPath={PRIVACY_NOTICES_ROUTE} />
      <Heading fontSize="2xl" fontWeight="semibold" mb={4} data-testid="header">
        {data.name}
      </Heading>

      <Box width={{ base: "100%", lg: "70%" }}>
        <Text fontSize="sm" mb={8}>
          Configure your privacy notice including consent mechanism, associated
          data uses and the locations in which this should be displayed to
          users.
        </Text>
        <Box data-testid="privacy-notice-detail-page">
          <PrivacyNoticeForm
            privacyNotice={data}
            availableTranslations={availableTranslations}
          />
        </Box>
      </Box>
    </Layout>
  );
};

export default PrivacyNoticeDetailPage;
