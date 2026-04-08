import { ChakraBox as Box, ChakraText as Text, Spin } from "fidesui";
import { useRouter } from "next/router";

import Layout from "~/features/common/Layout";
import { PRIVACY_NOTICES_ROUTE } from "~/features/common/nav/routes";
import { SidePanel } from "~/features/common/SidePanel";
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
      <>
        <SidePanel>
          <SidePanel.Identity title="Privacy notices" />
        </SidePanel>
        <Layout title="Privacy notice">
          <Spin />
        </Layout>
      </>
    );
  }

  if (!data) {
    return (
      <>
        <SidePanel>
          <SidePanel.Identity title="Privacy notices" />
        </SidePanel>
        <Layout title="Privacy notice">
          <Text>No privacy notice with id {noticeId} found.</Text>
        </Layout>
      </>
    );
  }

  return (
    <>
      <SidePanel>
        <SidePanel.Identity
          title={data.name}
          breadcrumbItems={[
            { title: "All privacy notices", href: PRIVACY_NOTICES_ROUTE },
            { title: data.name },
          ]}
          description="Configure your privacy notice including consent mechanism, data uses, and display locations."
        />
      </SidePanel>
      <Layout title={`Privacy notice ${data.name}`}>
        <Box
          width={{ base: "100%", lg: "70%" }}
          data-testid="privacy-notice-detail-page"
        >
          <PrivacyNoticeForm
            privacyNotice={data}
            availableTranslations={availableTranslations}
          />
        </Box>
      </Layout>
    </>
  );
};

export default PrivacyNoticeDetailPage;
