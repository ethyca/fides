import {
  DatasetLifecycleStatusEnum,
  DatasetLifecycleStatusResult,
} from "~/features/dataset-lifecycle/types";

export interface DatasetLifecycleProject {
  name?: string;
  urn: string;
  status: DatasetLifecycleStatusResult;
  lastUpdated: string;
}

interface DatasetLifecycleProjectQueryProps {
  pageIndex: number;
  pageSize: number;
  searchQuery: string;
}

const PROJECTS: DatasetLifecycleProject[] = [
  {
    name: "Project 1",
    urn: "project-1",
    status: {
      status: DatasetLifecycleStatusEnum.ADDED,
      detail: "New project",
    },
    lastUpdated: "2021-10-01T00:00:00Z",
  },
  {
    name: "Project 2",
    urn: "project-2",
    status: {
      status: DatasetLifecycleStatusEnum.IN_PROGRESS,
      detail: "In progress",
    },
    lastUpdated: "2021-10-02T00:00:00Z",
  },
  {
    name: "Project 3",
    urn: "project-3",
    status: {
      status: DatasetLifecycleStatusEnum.ATTENTION,
      detail: "Attention required",
    },
    lastUpdated: "2021-10-03T00:00:00Z",
  },
];

const useSpoofGetProjectsQuery = ({
  pageIndex,
  pageSize,
  searchQuery,
}: DatasetLifecycleProjectQueryProps) => {
  return {
    data: { items: PROJECTS, total: 0, page: 1, size: 50, pages: 1 },
    isLoading: false,
    isFetching: false,
  };
};

export default useSpoofGetProjectsQuery;
