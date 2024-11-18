import { ItemOption } from "common/dropdown/types";
import { capitalize } from "common/utils";
import React, { useMemo } from "react";
import { useDispatch, useSelector } from "react-redux";

import { FilterSelect } from "~/features/common/dropdown/FilterSelect";

import { DisabledStatus } from "../constants";
import {
  selectDatastoreConnectionFilters,
  setDisabledStatus,
} from "../datastore-connection.slice";

const DisabledStatusFilter = () => {
  // eslint-disable-next-line @typescript-eslint/naming-convention
  const { disabled_status } = useSelector(selectDatastoreConnectionFilters);

  const loadList = (): Map<string, ItemOption> => {
    const list = new Map<string, ItemOption>();
    const valuesList = Object.values(DisabledStatus).sort();
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
    dispatch(setDisabledStatus(value || ""));
  };

  return (
    <FilterSelect
      placeholder="Status"
      options={options}
      onChange={handleChange}
      defaultValue={disabled_status?.toString() || undefined}
    />
  );
};

export default DisabledStatusFilter;
