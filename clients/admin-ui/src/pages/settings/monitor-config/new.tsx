import Layout from "~/features/common/Layout";
import { MONITOR_CONFIG_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";

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
    </Layout>
  );
};
export default CreateMonitorConfig;
