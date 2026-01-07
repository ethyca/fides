import { AntFlex as Flex } from "fidesui";
import type { NextPage } from "next";

import ErrorPage from "~/features/common/errors/ErrorPage";
import Layout from "~/features/common/Layout";
import NotificationTabs from "~/features/common/NotificationTabs";
import PageHeader from "~/features/common/PageHeader";
import DigestConfigList from "~/features/digests/components/DigestConfigList";
import { useDigestConfigList } from "~/features/digests/hooks/useDigestConfigList";

const DigestsPage: NextPage = () => {
  const { error } = useDigestConfigList();

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage="A problem occurred while fetching your digests"
      />
    );
  }

  return (
    <Layout title="Notifications">
      <Flex vertical data-testid="digests-management">
        <PageHeader heading="Notifications" />
        <NotificationTabs />
        <DigestConfigList />
      </Flex>
    </Layout>
  );
};

export default DigestsPage;
