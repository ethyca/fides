import { useMemo } from "react";

export const useDiscoveredInfrastructureSystemsColumns = () => {
  const columns = useMemo(
    () => [
      {
        key: "name",
        dataIndex: "name",
        title: "System",
        sorter: true,
      },
    ],
    [],
  );

  return { columns };
};
