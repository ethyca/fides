import { AntSpin } from "fidesui";
import { CustomTypography } from "fidesui/src/hoc";
import { useRouter } from "next/router";

import Layout from "~/features/common/Layout";
import { MONITOR_CONFIG_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import MonitorTemplateForm from "~/features/monitors/MonitorTemplateForm";
import { useGetSharedMonitorConfigByIdQuery } from "~/features/monitors/shared-monitor-config.slice";

const EditMonitorTemplate = () => {
  const router = useRouter();
  const id = router.query.id as string;

  const { data, isLoading } = useGetSharedMonitorConfigByIdQuery({ id });

  return (
    <Layout title="Edit monitor config">
      <PageHeader
        heading="Monitor configs"
        breadcrumbItems={[
          {
            title: "All configs",
            href: MONITOR_CONFIG_ROUTE,
          },
          {
            title: data?.name ?? id,
          },
        ]}
      />
      <CustomTypography.Title level={2}>
        Edit {data?.name}
      </CustomTypography.Title>
      {isLoading ? (
        <AntSpin
          size="large"
          className="flex h-full items-center justify-center"
        />
      ) : (
        <MonitorTemplateForm config={data} />
      )}
    </Layout>
  );
};

export default EditMonitorTemplate;
