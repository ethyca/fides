import { setSystemType } from "connection-type/connection-type.slice";
import React, { useEffect, useRef } from "react";
import { useDispatch } from "react-redux";

import { FilterSelect } from "~/features/common/dropdown/FilterSelect";

import {
  CONNECTION_TYPE_FILTER_MAP,
  DEFAULT_CONNECTION_TYPE_FILTER,
} from "./constants";

const ConnectionTypeFilter = () => {
  const dispatch = useDispatch();
  const mounted = useRef(false);

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

  const options = useRef(
    [...CONNECTION_TYPE_FILTER_MAP].map(([key, value]) => ({
      value: value?.value,
      label: key,
    })),
  );

  return (
    <FilterSelect
      allowClear={false}
      options={options.current}
      onChange={handleChange}
      defaultValue=""
      data-testid="connection-type-filter"
    />
  );
};

export default ConnectionTypeFilter;
