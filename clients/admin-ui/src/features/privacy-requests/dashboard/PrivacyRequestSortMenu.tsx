import { AntButton, AntDropdown, Icons } from "fidesui";

import { FilterQueryParams } from "~/features/privacy-requests/dashboard/hooks/usePrivacyRequestsFilters";
import { ColumnSort } from "~/types/api";

export interface SortParams
  extends Pick<FilterQueryParams, "sort_field" | "sort_direction"> {}

interface PrivacyRequestSortMenuProps {
  sortState: SortParams;
  setSortState: (sortState: SortParams) => void;
}

enum SortOption {
  CREATED_AT_ASC = "created_at-asc",
  DAYS_LEFT_ASC = "days_left-asc",
  CREATED_AT_DESC = "created_at-desc",
  DAYS_LEFT_DESC = "days_left-desc",
}

const SORT_OPTIONS = [
  {
    label: "Time received (newest)",
    key: SortOption.CREATED_AT_DESC,
  },
  {
    label: "Time received (oldest)",
    key: SortOption.CREATED_AT_ASC,
  },
  {
    label: "Days left (shortest)",
    key: SortOption.DAYS_LEFT_ASC,
  },
  {
    label: "Days left (longest)",
    key: SortOption.DAYS_LEFT_DESC,
  },
];

const SORT_OPTION_STATE_MAP: Record<SortOption, SortParams> = {
  [SortOption.CREATED_AT_ASC]: {
    sort_field: "created_at",
    sort_direction: ColumnSort.ASC,
  },
  [SortOption.CREATED_AT_DESC]: {
    sort_field: "created_at",
    sort_direction: ColumnSort.DESC,
  },
  [SortOption.DAYS_LEFT_ASC]: {
    sort_field: "due_date",
    sort_direction: ColumnSort.ASC,
  },
  [SortOption.DAYS_LEFT_DESC]: {
    sort_field: "due_date",
    sort_direction: ColumnSort.DESC,
  },
};

const PrivacyRequestSortMenu = ({
  sortState,
  setSortState,
}: PrivacyRequestSortMenuProps) => {
  const selectedKey = Object.keys(SORT_OPTION_STATE_MAP).find((key) => {
    const value = SORT_OPTION_STATE_MAP[key as SortOption];
    return (
      value.sort_field === sortState.sort_field &&
      value.sort_direction === sortState.sort_direction
    );
  });

  return (
    <AntDropdown
      trigger={["click"]}
      menu={{
        items: SORT_OPTIONS.map((option) => ({
          ...option,
          onClick: () => setSortState(SORT_OPTION_STATE_MAP[option.key]),
        })),
        selectedKeys: selectedKey ? [selectedKey] : undefined,
      }}
    >
      <AntButton icon={<Icons.ChevronSort />} iconPosition="end">
        Sort
      </AntButton>
    </AntDropdown>
  );
};

export default PrivacyRequestSortMenu;
