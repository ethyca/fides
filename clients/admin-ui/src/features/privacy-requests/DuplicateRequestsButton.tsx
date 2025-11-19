import { AntButton as Button } from "fidesui";
import { useDispatch, useSelector } from "react-redux";

import { pluralize } from "~/features/common/utils";
import {
  selectPrivacyRequestFilters,
  setRequestStatus,
  useGetAllPrivacyRequestsQuery,
} from "~/features/privacy-requests/privacy-requests.slice";
import { PrivacyRequestStatus } from "~/types/api";

interface DuplicateRequestsButtonProps {
  className?: string;
  onFilterChange?: () => void;
}

/**
 * Component that displays a button to view duplicate privacy requests.
 * Only renders if there are duplicate requests and duplicates are not already being shown.
 * Fetches just 1 result to get the count.
 * Updates Redux state when clicked to filter for duplicate requests.
 */
export const DuplicateRequestsButton = ({
  className,
  onFilterChange,
}: DuplicateRequestsButtonProps) => {
  const dispatch = useDispatch();
  const filters = useSelector(selectPrivacyRequestFilters);

  const { data } = useGetAllPrivacyRequestsQuery({
    status: [PrivacyRequestStatus.DUPLICATE],
    page: 1,
    size: 1,
  });

  const duplicateCount = data?.total ?? 0;

  // Don't render if we're already in the 'show duplicates' view
  if (
    filters.status?.length === 1 &&
    filters.status[0] === PrivacyRequestStatus.DUPLICATE
  ) {
    return null;
  }

  // Don't render if there are no duplicates
  if (duplicateCount === 0) {
    return null;
  }

  const handleClick = () => {
    dispatch(setRequestStatus([PrivacyRequestStatus.DUPLICATE]));
    onFilterChange?.();
  };

  return (
    <Button
      type="text"
      onClick={handleClick}
      className={className}
      data-testid="duplicate-requests-button"
    >
      {duplicateCount} duplicate{" "}
      {pluralize(duplicateCount, "request", "requests")}
    </Button>
  );
};
