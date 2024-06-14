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

export const useRequestFilters = () => {
  const filters = useSelector(selectPrivacyRequestFilters);
  const dispatch = useDispatch();

  const handleStatusChange = (values: PrivacyRequestStatus[]) =>
    dispatch(setRequestStatus(values));

  const handleActionTypeChange = (values: ActionType[]) =>
    dispatch(setRequestActionType(values));

  const handleFromChange = (event: React.ChangeEvent<HTMLInputElement>) =>
    dispatch(setRequestFrom(event?.target.value));

  const handleToChange = (event: React.ChangeEvent<HTMLInputElement>) =>
    dispatch(setRequestTo(event?.target.value));

  const handleClearAllFilters = () => {
    dispatch(clearAllFilters());
  };

  return {
    handleStatusChange,
    handleActionTypeChange,
    handleFromChange,
    handleToChange,
    handleClearAllFilters,
    ...filters,
  };
};
