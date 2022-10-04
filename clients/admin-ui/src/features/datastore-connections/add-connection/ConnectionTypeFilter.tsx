import { useAppSelector } from "app/hooks";
import SelectDropdown from "common/dropdown/SelectDropdown";
import {
  selectConnectionTypeFilters,
  setSystemType,
} from "connection-type/connection-type.slice";
import React, { useEffect, useRef } from "react";
import { useDispatch } from "react-redux";

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
  const mounted = useRef(false);
  const filters = useAppSelector(selectConnectionTypeFilters);

  const handleChange = (value?: string) => {
    dispatch(setSystemType(value || DEFAULT_CONNECTION_TYPE_FILTER));
  };

  useEffect(() => {
    mounted.current = true;
    return () => {
      dispatch(setSystemType(DEFAULT_CONNECTION_TYPE_FILTER));
      mounted.current = false;
    };
  }, [dispatch]);

  return (
    <SelectDropdown
      enableSorting={false}
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
