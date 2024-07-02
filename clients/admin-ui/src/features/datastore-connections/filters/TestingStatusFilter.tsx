import SelectDropdown from "common/dropdown/SelectDropdown";
import { ItemOption } from "common/dropdown/types";
import { capitalize } from "common/utils";
import { Box } from "fidesui";
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

const TestingStatusFilter = ({ width }: TestingStatusFilterProps) => {
  // eslint-disable-next-line @typescript-eslint/naming-convention
  const { test_status } = useSelector(selectDatastoreConnectionFilters);

  const loadList = (): Map<string, ItemOption> => {
    const list = new Map<string, ItemOption>();
    const valuesList = Object.values(TestingStatus).sort();
    valuesList.forEach((value) => {
      list.set(capitalize(value), { value });
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
    <Box>
      <SelectDropdown
        label="Testing Status"
        list={list}
        menuButtonProps={{ width }}
        onChange={handleChange}
        selectedValue={test_status?.toString()}
      />
    </Box>
  );
};

export default TestingStatusFilter;
