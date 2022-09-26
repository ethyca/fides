import SelectDropdown from "common/dropdown/SelectDropdown";
import { ItemOption } from "common/dropdown/types";
import { capitalize } from "common/utils";
import React, { useMemo } from "react";
import { useDispatch, useSelector } from "react-redux";

import { DisabledStatus } from "../constants";
import {
  selectDatastoreConnectionFilters,
  setDisabledStatus,
} from "../datastore-connection.slice";

export type DisabledStatusFilterProps = {
  width?: string;
};

const DisabledStatusFilter: React.FC<DisabledStatusFilterProps> = ({
  width,
}) => {
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

  // Hooks
  const dispatch = useDispatch();

  // Listeners
  const handleChange = (value?: string) => {
    dispatch(setDisabledStatus(value || ""));
  };

  return (
    <SelectDropdown
      label="Status"
      list={list}
      onChange={handleChange}
      selectedValue={disabled_status?.toString()}
      width={width}
    />
  );
};

export default DisabledStatusFilter;
