import { Center, Spinner, Text } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { ReactNode } from "react";

import Layout from "~/features/common/Layout";
import { PRIVACY_REQUESTS_ROUTE } from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";
import { useGetAllPrivacyRequestsQuery } from "~/features/privacy-requests";
import PrivacyRequest from "~/features/privacy-requests/PrivacyRequest";

const PrivacyRequests: NextPage = () => {
  const router = useRouter();
  const { id = "" } = router.query;
  const { data, isLoading, isUninitialized } = useGetAllPrivacyRequestsQuery(
    {
      id: Array.isArray(id) ? id[0] : id,
      verbose: true,
    },
    {
      skip: id === "",
    },
  );

  let content: ReactNode;
  if (isUninitialized || isLoading) {
    content = (
      <Center>
        <Spinner />
      </Center>
    );
  } else {
    content =
      !data || data?.items.length === 0 ? (
        <Text>404 no privacy request found</Text>
      ) : (
        <PrivacyRequest data={data?.items[0]!} />
      );
  }

  return (
    <Layout title={`Privacy Request - ${id}`}>
      <PageHeader
        heading="Privacy Requests"
        breadcrumbItems={[
          { title: "All requests", href: PRIVACY_REQUESTS_ROUTE },
          { title: "Request details" },
        ]}
      />
      {content}
    </Layout>
  );
};
export default PrivacyRequests;
