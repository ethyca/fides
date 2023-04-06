import { Box } from "@fidesui/react";
import { useRouter } from "next/router";

import Layout from "~/features/common/Layout";

const PrivacyNoticeDetailPage = () => {
  const router = useRouter();

  let noticeId = "";
  if (router.query.id) {
    noticeId = Array.isArray(router.query.id)
      ? router.query.id[0]
      : router.query.id;
  }

  return (
    <Layout title={`Privacy notice ${noticeId}`}>
      <Box data-testid="privacy-notice-detail-page">
        Work in progress, stay tuned!
      </Box>
    </Layout>
  );
};

export default PrivacyNoticeDetailPage;
