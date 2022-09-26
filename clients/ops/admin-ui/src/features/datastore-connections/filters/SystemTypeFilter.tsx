import SelectDropdown from "common/dropdown/SelectDropdown";
import { ItemOption } from "common/dropdown/types";
import { capitalize } from "common/utils";
import React, { useMemo } from "react";
import { useDispatch, useSelector } from "react-redux";

import { SystemType } from "../constants";
import {
  selectDatastoreConnectionFilters,
  setSystemType,
} from "../datastore-connection.slice";

export type SystemTypeFilterProps = {
  width?: string;
};

const SystemTypeFilter: React.FC<SystemTypeFilterProps> = ({ width }) => {
  // eslint-disable-next-line @typescript-eslint/naming-convention
  const { system_type } = useSelector(selectDatastoreConnectionFilters);

  const loadList = (): Map<string, ItemOption> => {
    const list = new Map<string, ItemOption>();
    const valuesList = Object.values(SystemType).sort();
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
    dispatch(setSystemType(value || ""));
  };

  return (
    <SelectDropdown
      label="System Type"
      list={list}
      onChange={handleChange}
      selectedValue={system_type?.toString()}
      width={width}
    />
  );
};

export default SystemTypeFilter;
