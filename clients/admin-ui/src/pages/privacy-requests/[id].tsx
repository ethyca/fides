import { Flex, Spin } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import ErrorPage from "~/features/common/errors/ErrorPage";
import Layout from "~/features/common/Layout";
import { PRIVACY_REQUESTS_ROUTE } from "~/features/common/nav/routes";
import { SidePanel } from "~/features/common/SidePanel";
import { useGetAllPrivacyRequestsQuery } from "~/features/privacy-requests";
import PrivacyRequest from "~/features/privacy-requests/PrivacyRequest";
import PrivacyRequestActionsDropdown from "~/features/privacy-requests/PrivacyRequestActionsDropdown";

const PrivacyRequests: NextPage = () => {
  const router = useRouter();
  const privacyRequestId = router.query.id as string;

  const { data, isLoading, error } = useGetAllPrivacyRequestsQuery(
    {
      id: privacyRequestId,
      verbose: true,
    },
    {
      skip: !privacyRequestId,
    },
  );

  const privacyRequest = data?.items[0] || null;

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage={`A problem occurred while fetching the privacy request ${privacyRequestId}`}
      />
    );
  }

  return (
    <>
      <SidePanel>
        <SidePanel.Identity
          title="Privacy Requests"
          breadcrumbItems={[
            { title: "All requests", href: PRIVACY_REQUESTS_ROUTE },
            { title: "Request details" },
          ]}
        />
      </SidePanel>
      <Layout title={`Privacy Request - ${privacyRequestId}`}>
        {!!privacyRequest && (
          <Flex justify="end" style={{ marginBottom: 16 }}>
            <PrivacyRequestActionsDropdown privacyRequest={privacyRequest} />
          </Flex>
        )}
        {isLoading && <Spin />}
        {!isLoading && privacyRequest && (
          <PrivacyRequest data={privacyRequest} />
        )}
      </Layout>
    </>
  );
};

export default PrivacyRequests;
