export interface ListDataItem {
  key: string;
  title: string;
  description: string;
  status: "active" | "completed";
  locked?: boolean;
}

export const listData: ListDataItem[] = [
  {
    key: "1",
    title: "Task Alpha",
    description: "Complete the first phase of development",
    status: "active",
  },
  {
    key: "2",
    title: "Task Beta",
    description: "Review and test the implementation",
    status: "completed",
  },
  {
    key: "3",
    title: "Task Gamma",
    description: "Deploy to staging environment",
    status: "completed",
  },
  {
    key: "4",
    title: "Task Delta (Locked)",
    description: "This task is locked and cannot be selected",
    status: "active",
    locked: true,
  },
  {
    key: "5",
    title: "Task Epsilon",
    description: "Monitor production metrics",
    status: "active",
  },
];
