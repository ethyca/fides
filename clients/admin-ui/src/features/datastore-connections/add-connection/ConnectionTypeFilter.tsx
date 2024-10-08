import SelectDropdown from "common/dropdown/SelectDropdown";
import {
  selectConnectionTypeFilters,
  setSystemType,
} from "connection-type/connection-type.slice";
import { Box } from "fidesui";
import React, { useEffect, useRef } from "react";
import { useDispatch } from "react-redux";

import { useAppSelector } from "~/app/hooks";

import {
  CONNECTION_TYPE_FILTER_MAP,
  DEFAULT_CONNECTION_TYPE_FILTER,
} from "./constants";

const ConnectionTypeFilter = () => {
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
    <Box>
      <SelectDropdown
        enableSorting={false}
        hasClear={false}
        label="Show all connectors"
        list={CONNECTION_TYPE_FILTER_MAP}
        onChange={handleChange}
        selectedValue={filters.system_type || DEFAULT_CONNECTION_TYPE_FILTER}
      />
    </Box>
  );
};

export default ConnectionTypeFilter;
