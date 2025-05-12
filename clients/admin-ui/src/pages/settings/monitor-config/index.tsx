import { AntButton } from "fidesui";
import { useRouter } from "next/router";

import Layout from "~/features/common/Layout";
import {
  CREATE_MONITOR_CONFIG_ROUTE,
  MONITOR_CONFIG_ROUTE,
} from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";

const MonitorConfigTable = () => {
  const router = useRouter();
  return (
    <Layout title="Monitor configs">
      <PageHeader
        heading="Monitor configs"
        breadcrumbItems={[
          {
            title: "All configs",
          },
        ]}
      />
      <div>
        Configuring monitor config...
        <AntButton onClick={() => router.push(CREATE_MONITOR_CONFIG_ROUTE)}>
          Add new
        </AntButton>
        <AntButton onClick={() => router.push(`${MONITOR_CONFIG_ROUTE}/1`)}>
          Edit config 1
        </AntButton>
      </div>
    </Layout>
  );
};
export default MonitorConfigTable;
