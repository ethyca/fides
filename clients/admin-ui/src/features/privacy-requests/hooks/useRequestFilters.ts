import { useCallback, useMemo } from "react";
import { useDispatch, useSelector } from "react-redux";

import { SubjectRequestStatusMap } from "../constants";
import {
  clearAllFilters,
  selectPrivacyRequestFilters,
  setRequestFrom,
  setRequestStatus,
  setRequestTo,
} from "../privacy-requests.slice";
import { PrivacyRequestStatus } from "../types";

export const useRequestFilters = () => {
  const filters = useSelector(selectPrivacyRequestFilters);
  const dispatch = useDispatch();

  const handleStatusChange = useCallback(
    (values: string[]) => {
      const list: PrivacyRequestStatus[] = [];
      values.forEach((v) => {
        SubjectRequestStatusMap.forEach((value, key) => {
          if (key === v) {
            list.push(value as PrivacyRequestStatus);
          }
        });
      });
      dispatch(setRequestStatus(list));
    },
    [dispatch]
  );

  const handleFromChange = (event: React.ChangeEvent<HTMLInputElement>) =>
    dispatch(setRequestFrom(event?.target.value));

  const handleToChange = (event: React.ChangeEvent<HTMLInputElement>) =>
    dispatch(setRequestTo(event?.target.value));

  const handleClearAllFilters = () => {
    dispatch(clearAllFilters());
  };

  const loadStatusList = (values: string[]): Map<string, boolean> => {
    const list = new Map<string, boolean>();
    SubjectRequestStatusMap.forEach((value, key) => {
      let result = false;
      if (values.includes(value)) {
        result = true;
      }
      list.set(key, result);
    });
    return list;
  };

  // Load the status list
  const statusList = useMemo(
    () => loadStatusList(filters.status || []),
    [filters.status]
  );

  // Filter the selected status list
  const selectedStatusList = new Map(
    [...statusList].filter(([, v]) => v === true)
  );

  return {
    handleStatusChange,
    handleFromChange,
    handleToChange,
    handleClearAllFilters,
    loadStatusList,
    ...filters,
    selectedStatusList,
    statusList,
  };
};
