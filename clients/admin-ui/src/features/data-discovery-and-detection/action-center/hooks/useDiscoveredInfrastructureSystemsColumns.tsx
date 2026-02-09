import { ColumnsType } from "fidesui";
import { useMemo } from "react";

import { SystemStagedResourcesAggregateRecord } from "~/types/api";

import { isIdentityProviderColumns } from "../utils/columnBuilders";

interface UseDiscoveredInfrastructureSystemsColumnsProps {
  isOktaApp?: boolean;
  rowClickUrl?: (record: SystemStagedResourcesAggregateRecord) => string;
}

export const useDiscoveredInfrastructureSystemsColumns = ({
  rowClickUrl,
}: UseDiscoveredInfrastructureSystemsColumnsProps = {}) => {
  const columns: ColumnsType<SystemStagedResourcesAggregateRecord> =
    useMemo(() => {
      return isIdentityProviderColumns({ rowClickUrl });
    }, [rowClickUrl]);

  return { columns };
};
