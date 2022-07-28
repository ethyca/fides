import SelectDropdown from "common/dropdown/SelectDropdown";
import { capitalize } from "common/utils";
import React, { useMemo } from "react";
import { useDispatch, useSelector } from "react-redux";

import { TestingStatus } from "../constants";
import {
  selectDatastoreConnectionFilters,
  setTestingStatus,
} from "../datastore-connection.slice";

export type TestingStatusFilterProps = {
  width?: string;
};

const TestingStatusFilter: React.FC<TestingStatusFilterProps> = ({ width }) => {
  // eslint-disable-next-line @typescript-eslint/naming-convention
  const { test_status } = useSelector(selectDatastoreConnectionFilters);

  const loadList = (): Map<string, string> => {
    const list = new Map<string, string>();
    const valuesList = Object.values(TestingStatus).sort();
    valuesList.forEach((value) => {
      list.set(capitalize(value), value);
    });
    return list;
  };

  const list = useMemo(() => loadList(), []);

  // Hooks
  const dispatch = useDispatch();

  // Listeners
  const handleChange = (value?: string) => {
    dispatch(setTestingStatus(value || ""));
  };

  return (
    <SelectDropdown
      label="Testing Status"
      list={list}
      onChange={handleChange}
      selectedValue={test_status?.toString()}
      width={width}
    />
  );
};

export default TestingStatusFilter;
