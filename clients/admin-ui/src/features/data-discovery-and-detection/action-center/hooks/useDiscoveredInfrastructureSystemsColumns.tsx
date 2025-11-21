import { useMemo } from "react";

import { SystemStagedResourcesAggregateRecord } from "~/types/api";

interface UseDiscoveredInfrastructureSystemsColumnsConfig {
  rowClickUrl: (record: SystemStagedResourcesAggregateRecord) => string;
}

export const useDiscoveredInfrastructureSystemsColumns = ({
  rowClickUrl,
}: UseDiscoveredInfrastructureSystemsColumnsConfig) => {
  const columns = useMemo(
    () => [
      {
        key: "name",
        dataIndex: "name",
        title: "System",
        sorter: true,
        onCell: (record: SystemStagedResourcesAggregateRecord) => ({
          onClick: () => {
            window.location.href = rowClickUrl(record);
          },
          style: { cursor: "pointer" },
        }),
      },
    ],
    [rowClickUrl],
  );

  return { columns };
};
