import { CustomTypography } from "fidesui/src/hoc";

import Layout from "~/features/common/Layout";
import { MONITOR_CONFIG_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import MonitorTemplateForm from "~/features/monitors/MonitorTemplateForm";

const CreateMonitorConfig = () => {
  return (
    <Layout title="Create monitor config">
      <PageHeader
        heading="Monitor configs"
        breadcrumbItems={[
          {
            title: "All configs",
            href: MONITOR_CONFIG_ROUTE,
          },
          {
            title: "Create new",
          },
        ]}
      />

      <CustomTypography.Title level={2}>
        Create new monitor config
      </CustomTypography.Title>
      <MonitorTemplateForm />
    </Layout>
  );
};
export default CreateMonitorConfig;
