import { useMemo } from "react";
import { useDispatch, useSelector } from "react-redux";

import { ActionType, PrivacyRequestStatus } from "~/types/api";

import {
  clearAllFilters,
  selectPrivacyRequestFilters,
  setRequestActionType,
  setRequestFrom,
  setRequestStatus,
  setRequestTo,
} from "../privacy-requests.slice";

export const useRequestFilters = (onFilterChange: () => void) => {
  const filters = useSelector(selectPrivacyRequestFilters);
  const dispatch = useDispatch();

  const handleStatusChange = (values: PrivacyRequestStatus[]) => {
    dispatch(setRequestStatus(values));
    onFilterChange();
  };

  const handleActionTypeChange = (values: ActionType[]) => {
    dispatch(setRequestActionType(values));
    onFilterChange();
  };

  const handleFromChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    dispatch(setRequestFrom(event?.target.value));
    onFilterChange();
  };

  const handleToChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    dispatch(setRequestTo(event?.target.value));
    onFilterChange();
  };

  const handleClearAllFilters = () => {
    dispatch(clearAllFilters());
    onFilterChange();
  };

  const anyFiltersApplied = useMemo(() => {
    return (
      filters.action_type?.length ||
      filters.from !== "" ||
      filters.to !== "" ||
      filters.status?.length
    );
  }, [filters]);

  return {
    handleStatusChange,
    handleActionTypeChange,
    handleFromChange,
    handleToChange,
    handleClearAllFilters,
    anyFiltersApplied,
    ...filters,
  };
};
