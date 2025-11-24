import { AntColumnsType as ColumnsType } from "fidesui";
import { useMemo } from "react";

import { SystemStagedResourcesAggregateRecord } from "~/types/api";

import { isIdentityProviderColumns } from "../utils/columnBuilders";

interface UseDiscoveredInfrastructureSystemsColumnsProps {
  isOktaApp?: boolean;
  rowClickUrl?: (record: SystemStagedResourcesAggregateRecord) => string;
}

export const useDiscoveredInfrastructureSystemsColumns = ({
  isOktaApp = false,
  rowClickUrl,
}: UseDiscoveredInfrastructureSystemsColumnsProps = {}) => {
  const columns: ColumnsType<SystemStagedResourcesAggregateRecord> =
    useMemo(() => {
      if (isOktaApp) {
        // Use identity provider columns for Okta apps
        return isIdentityProviderColumns({ rowClickUrl });
      }

      // Default infrastructure columns for non-Okta monitors
      return [
        {
          key: "name",
          dataIndex: "name",
          title: "System",
          sorter: true,
        },
      ];
    }, [isOktaApp, rowClickUrl]);

  return { columns };
};
