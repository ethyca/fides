import { Center, Spinner, Text } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import Layout from "~/features/common/Layout";
import { PRIVACY_REQUESTS_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { useGetAllPrivacyRequestsQuery } from "~/features/privacy-requests";
import PrivacyRequest from "~/features/privacy-requests/PrivacyRequest";
import PrivacyRequestActionsDropdown from "~/features/privacy-requests/PrivacyRequestActionsDropdown";

const PrivacyRequests: NextPage = () => {
  const router = useRouter();
  const privacyRequestId = router.query.id as string;

  const { data, isLoading } = useGetAllPrivacyRequestsQuery(
    {
      id: privacyRequestId,
      verbose: true,
    },
    {
      skip: !privacyRequestId,
    },
  );

  const privacyRequest = data?.items[0] || null;

  return (
    <Layout title={`Privacy Request - ${privacyRequestId}`}>
      <PageHeader
        heading="Privacy Requests"
        breadcrumbItems={[
          { title: "All requests", href: PRIVACY_REQUESTS_ROUTE },
          { title: "Request details" },
        ]}
        rightContent={
          !!privacyRequest && (
            <PrivacyRequestActionsDropdown privacyRequest={privacyRequest} />
          )
        }
      />
      {isLoading && (
        <Center>
          <Spinner />
        </Center>
      )}
      {!isLoading && !privacyRequest && (
        <Text>404 no privacy request found</Text>
      )}
      {!isLoading && privacyRequest && <PrivacyRequest data={privacyRequest} />}
    </Layout>
  );
};

export default PrivacyRequests;
