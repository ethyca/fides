import React from "react";
import { useSelector } from "react-redux";

import { useAppDispatch } from "~/app/hooks";
import { FilterSelect } from "~/features/common/dropdown/FilterSelect";

import { CONNECTION_TYPE_FILTER_MAP } from "../add-connection/constants";
import {
  selectDatastoreConnectionFilters,
  setSystemType,
} from "../datastore-connection.slice";

const SystemTypeFilter = () => {
  // eslint-disable-next-line @typescript-eslint/naming-convention
  const { system_type } = useSelector(selectDatastoreConnectionFilters);

  const list = new Map(CONNECTION_TYPE_FILTER_MAP);
  list.delete("Show all");
  const options = [...list].map(([key, value]) => {
    return {
      value: value.value,
      label: key,
    };
  });

  // Hooks
  const dispatch = useAppDispatch();

  // Listeners
  const handleChange = (value?: string) => {
    dispatch(setSystemType(value || ""));
  };

  return (
    <FilterSelect
      placeholder="System Type"
      options={options}
      onChange={handleChange}
      defaultValue={system_type?.toString() || undefined}
      data-testid="system-type-filter"
    />
  );
};

export default SystemTypeFilter;
