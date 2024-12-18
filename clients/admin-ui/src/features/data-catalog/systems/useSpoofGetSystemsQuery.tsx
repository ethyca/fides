import {
  DatasetLifecycleStatusEnum,
  DatasetLifecycleStatusResult,
} from "~/features/data-catalog/types";
import {
  AccessLevel,
  ConnectionConfigurationResponse,
  ConnectionType,
} from "~/types/api";

export interface DatasetLifecycleSystem {
  name?: string;
  id: string;
  status: DatasetLifecycleStatusResult;
  changes: number;
  lastUpdated: string;
  dataUses: string[];
  integration?: ConnectionConfigurationResponse;
}

interface DatasetLifecycleSystemQueryProps {
  pageIndex: number;
  pageSize: number;
  searchQuery: string;
}

const SYSTEMS: DatasetLifecycleSystem[] = [
  {
    name: "System 1",
    id: "system-1",
    status: {
      status: DatasetLifecycleStatusEnum.ADDED,
      detail: "New system",
    },
    changes: 0,
    lastUpdated: "2021-10-01T00:00:00Z",
    dataUses: ["Data use 1", "Data use 2"],
    integration: {
      name: "Test",
      key: "test",
      connection_type: ConnectionType.BIGQUERY,
      access: AccessLevel.READ,
      created_at: "2021-10-01T00:00:00Z",
    },
  },
  {
    name: "System 2",
    id: "system-2",
    status: {
      status: DatasetLifecycleStatusEnum.IN_PROGRESS,
      detail: "In progress",
    },
    changes: 1,
    lastUpdated: "2021-10-02T00:00:00Z",
    dataUses: ["Data use 1"],
  },
  {
    name: "System 3",
    id: "system-3",
    status: {
      status: DatasetLifecycleStatusEnum.ATTENTION,
      detail: "Requires attention",
    },
    changes: 2,
    lastUpdated: "2021-10-03T00:00:00Z",
    dataUses: ["Data use 2"],
    integration: {
      name: "Test",
      key: "test",
      connection_type: ConnectionType.BIGQUERY,
      access: AccessLevel.READ,
      created_at: "2021-10-01T00:00:00Z",
    },
  },
];

const useSpoofGetSystemsQuery = ({
  pageIndex,
  pageSize,
  searchQuery,
}: DatasetLifecycleSystemQueryProps) => {
  return {
    data: { items: SYSTEMS, total: 0, page: 1, size: 50, pages: 1 },
    isLoading: false,
    isFetching: false,
  };
};

export default useSpoofGetSystemsQuery;
