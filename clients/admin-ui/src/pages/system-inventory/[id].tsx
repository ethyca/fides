import { Tabs } from "fidesui";
import { NextPage } from "next";
import { useRouter } from "next/router";

import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
import SystemDetailAlerts from "~/features/system-inventory/detail/SystemDetailAlerts";
import SystemDetailHeader from "~/features/system-inventory/detail/SystemDetailHeader";
import SystemDetailStats from "~/features/system-inventory/detail/SystemDetailStats";
import AssetsTab from "~/features/system-inventory/detail/tabs/AssetsTab";
import DataFlowTab from "~/features/system-inventory/detail/tabs/DataFlowTab";
import DataUsesTab from "~/features/system-inventory/detail/tabs/DataUsesTab";
import HistoryTab from "~/features/system-inventory/detail/tabs/HistoryTab";
import InformationTab from "~/features/system-inventory/detail/tabs/InformationTab";
import IntegrationsTab from "~/features/system-inventory/detail/tabs/IntegrationsTab";
import OverviewTab from "~/features/system-inventory/detail/tabs/OverviewTab";
import { useSystemDetail } from "~/features/system-inventory/hooks/useSystemDetail";

const SystemDetailPage: NextPage = () => {
  const router = useRouter();
  const { id } = router.query;
  const system = useSystemDetail(id as string | undefined);

  if (!system) {
    return null;
  }

  const tabItems = [
    {
      key: "overview",
      label: "Overview",
      children: <OverviewTab system={system} />,
    },
    {
      key: "information",
      label: "Information",
      children: <InformationTab system={system} />,
    },
    {
      key: "data-uses",
      label: "Data uses",
      children: <DataUsesTab system={system} />,
    },
    {
      key: "data-flow",
      label: "Data flow",
      children: <DataFlowTab system={system} />,
    },
    {
      key: "integrations",
      label: "Integrations",
      children: <IntegrationsTab system={system} />,
    },
    {
      key: "assets",
      label: "Assets",
      children: <AssetsTab system={system} />,
    },
    {
      key: "history",
      label: "History",
      children: <HistoryTab system={system} />,
    },
  ];

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
      <SystemDetailAlerts system={system} />
      <SystemDetailStats system={system} />
      <Tabs items={tabItems} defaultActiveKey="overview" />
    </FixedLayout>
  );
};

export default SystemDetailPage;
