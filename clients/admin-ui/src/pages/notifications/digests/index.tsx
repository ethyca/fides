import { Flex } from "fidesui";
import type { NextPage } from "next";

import ErrorPage from "~/features/common/errors/ErrorPage";
import Layout from "~/features/common/Layout";
import NotificationTabs from "~/features/common/NotificationTabs";
import { SidePanel } from "~/features/common/SidePanel";
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
    <>
      <SidePanel>
        <SidePanel.Identity title="Notifications" />
      </SidePanel>
      <Layout title="Notifications">
        <Flex vertical data-testid="digests-management">
          <NotificationTabs />
          <DigestConfigList />
        </Flex>
      </Layout>
    </>
  );
};

export default DigestsPage;
