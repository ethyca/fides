import { AntButton, AntSpin, AntTable } from "fidesui";
import { CustomTypography } from "fidesui/src/hoc";
import { useRouter } from "next/router";

import Layout from "~/features/common/Layout";
import { CREATE_MONITOR_CONFIG_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { useGetSharedMonitorConfigsQuery } from "~/features/monitors/shared-monitor-config.slice";
import useSharedMonitorConfigColumns from "~/pages/settings/monitor-config/useSharedMonitorConfigColumns";

const MonitorConfigTable = () => {
  const { data, isLoading } = useGetSharedMonitorConfigsQuery({
    page: 1,
    size: 10,
  });

  const columns = useSharedMonitorConfigColumns();
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
      <CustomTypography.Paragraph>
        Shared monitor configs can be applied to monitors to customize
        classification.
      </CustomTypography.Paragraph>
      <AntButton
        type="primary"
        onClick={() => router.push(CREATE_MONITOR_CONFIG_ROUTE)}
        className="mb-2 self-end"
      >
        Create new
      </AntButton>
      {isLoading ? (
        <AntSpin
          size="large"
          className="flex h-full items-center justify-center"
        />
      ) : (
        <AntTable columns={columns} dataSource={data?.items} size="small" />
      )}
    </Layout>
  );
};
export default MonitorConfigTable;
