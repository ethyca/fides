import SelectDropdown from "common/dropdown/SelectDropdown";
import React from "react";
import { useDispatch } from "react-redux";

import { useAppSelector } from "../../../app/hooks";
import {
  selectConnectionTypeFilters,
  setSystemType,
} from "../../connection-type";
import {
  CONNECTION_TYPE_FILTER_MAP,
  DEFAULT_CONNECTION_TYPE_FILTER,
} from "./constants";

export type ConnectionTypeFilterProps = {
  width?: string;
};

const ConnectionTypeFilter: React.FC<ConnectionTypeFilterProps> = ({
  width,
}) => {
  const dispatch = useDispatch();
  const filters = useAppSelector(selectConnectionTypeFilters);

  const handleChange = (value?: string) => {
    dispatch(setSystemType(value || ""));
  };

  return (
    <SelectDropdown
      hasClear={false}
      label="Show all connectors"
      list={CONNECTION_TYPE_FILTER_MAP}
      onChange={handleChange}
      selectedValue={filters.system_type || DEFAULT_CONNECTION_TYPE_FILTER}
      width={width}
    />
  );
};

export default ConnectionTypeFilter;
