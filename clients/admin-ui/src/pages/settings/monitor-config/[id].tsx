import { useRouter } from "next/router";

import Layout from "~/features/common/Layout";
import { MONITOR_CONFIG_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";

const MonitorTemplateForm = () => {
  const router = useRouter();
  const id = router.query.id as string;
  console.log(id);

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
            title: id,
          },
        ]}
      />
    </Layout>
  );
};

export default MonitorTemplateForm;
