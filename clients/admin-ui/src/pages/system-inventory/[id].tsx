import { NextPage } from "next";
import { useRouter } from "next/router";

import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
import SystemDetailContent from "~/features/system-inventory/components/SystemDetailContent";
import SystemBriefingBanner from "~/features/system-inventory/detail/SystemBriefingBanner";
import SystemDetailDashboardV2 from "~/features/system-inventory/detail/SystemDetailDashboardV2";
import SystemDetailHeader from "~/features/system-inventory/detail/SystemDetailHeader";
import { useSystemDetail } from "~/features/system-inventory/hooks/useSystemDetail";

const SystemDetailPage: NextPage = () => {
  const router = useRouter();
  const { id } = router.query;
  const system = useSystemDetail(id as string | undefined);

  if (!system) {
    return null;
  }

  return (
    <FixedLayout title={system.name}>
      <PageHeader
        heading="Systems"
        breadcrumbItems={[
          { title: "All systems", href: "/system-inventory" },
          { title: system.name },
        ]}
      />
      <SystemDetailHeader system={system} />
      <SystemBriefingBanner system={system} />
      <SystemDetailDashboardV2 system={system} />
      <SystemDetailContent system={system} />
    </FixedLayout>
  );
};

export default SystemDetailPage;
