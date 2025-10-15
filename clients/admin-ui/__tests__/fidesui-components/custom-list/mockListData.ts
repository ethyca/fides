export interface TestDataItem {
  key: string;
  title: string;
  description: string;
  locked?: boolean;
}

export const MOCK_LIST_DATA: TestDataItem[] = [
  {
    key: "1",
    title: "Item One",
    description: "First item description",
  },
  {
    key: "2",
    title: "Item Two",
    description: "Second item description",
  },
  {
    key: "3",
    title: "Item Three",
    description: "Third item description",
  },
  {
    key: "4",
    title: "Item Four (Locked)",
    description: "This item is locked",
    locked: true,
  },
  {
    key: "5",
    title: "Item Five",
    description: "Fifth item description",
  },
];
