export interface ListDataItem {
  key: string;
  title: string;
  description: string;
  status: "active" | "completed";
  locked?: boolean;
}

export const MOCK_LIST_DATA: ListDataItem[] = [
  {
    key: "1",
    title: "Item One",
    description: "First item description",
    status: "active",
  },
  {
    key: "2",
    title: "Item Two",
    description: "Second item description",
    status: "completed",
  },
  {
    key: "3",
    title: "Item Three",
    description: "Third item description",
    status: "completed",
  },
  {
    key: "4",
    title: "Item Four (Locked)",
    description: "This item is locked",
    status: "active",
    locked: true,
  },
  {
    key: "5",
    title: "Item Five",
    description: "Fifth item description",
    status: "active",
  },
];
