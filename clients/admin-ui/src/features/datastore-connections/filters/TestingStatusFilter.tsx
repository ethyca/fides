import { ItemOption } from "common/dropdown/types";
import { capitalize } from "common/utils";
import React, { useMemo } from "react";
import { useDispatch, useSelector } from "react-redux";

import { FilterSelect } from "~/features/common/dropdown/FilterSelect";

import { TestingStatus } from "../constants";
import {
  selectDatastoreConnectionFilters,
  setTestingStatus,
} from "../datastore-connection.slice";

const TestingStatusFilter = () => {
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
  const options = [...list].map(([key, value]) => {
    return {
      value: value.value,
      label: key,
    };
  });

  // Hooks
  const dispatch = useDispatch();

  // Listeners
  const handleChange = (value?: string) => {
    dispatch(setTestingStatus(value || ""));
  };

  return (
    <FilterSelect
      placeholder="Testing Status"
      options={options}
      onChange={handleChange}
      defaultValue={test_status?.toString() || undefined}
    />
  );
};

export default TestingStatusFilter;
