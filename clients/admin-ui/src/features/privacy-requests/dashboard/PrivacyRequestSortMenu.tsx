import { AntSelect as Select, Icons } from "fidesui";

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
    value: SortOption.CREATED_AT_DESC,
  },
  {
    label: "Time received (oldest)",
    value: SortOption.CREATED_AT_ASC,
  },
  {
    label: "Days left (shortest)",
    value: SortOption.DAYS_LEFT_ASC,
  },
  {
    label: "Days left (longest)",
    value: SortOption.DAYS_LEFT_DESC,
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
  const selectedKey = Object.values(SortOption).find((option) => {
    const value = SORT_OPTION_STATE_MAP[option];
    return (
      value.sort_field === sortState.sort_field &&
      value.sort_direction === sortState.sort_direction
    );
  });

  const { sort_direction: sortDirection } = sortState;

  return (
    <Select
      aria-label="Sort requests"
      options={SORT_OPTIONS}
      value={selectedKey}
      onChange={(value) => setSortState(SORT_OPTION_STATE_MAP[value])}
      placeholder="Sort by..."
      className="w-64"
      prefix={
        sortDirection === ColumnSort.ASC ? (
          <Icons.SortAscending />
        ) : (
          <Icons.SortDescending />
        )
      }
    />
  );
};

export default PrivacyRequestSortMenu;
