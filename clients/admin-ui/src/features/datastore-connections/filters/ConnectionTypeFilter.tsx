import MultiSelectDropdown from "common/dropdown/MultiSelectDropdown";
import React, { useCallback, useMemo } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { selectConnectionTypeState } from "~/features/connection-type";

import {
  selectDatastoreConnectionFilters,
  setConnectionType,
} from "../datastore-connection.slice";

export type ConnectionTypeFilterProps = {
  width?: string;
};

const ConnectionTypeFilter = ({ width }: ConnectionTypeFilterProps) => {
  const { connectionOptions } = useAppSelector(selectConnectionTypeState);

  // eslint-disable-next-line @typescript-eslint/naming-convention
  const { connection_type } = useAppSelector(selectDatastoreConnectionFilters);

  const loadList = useCallback((): Map<string, boolean> => {
    const list = new Map<string, boolean>();
    connectionOptions.forEach((option) => {
      let result = false;
      if (connection_type?.includes(option.identifier)) {
        result = true;
      }
      list.set(option.human_readable, result);
    });

    return list;
  }, [connectionOptions, connection_type]);

  const list = useMemo(() => loadList(), [loadList]);
  const selectedList = new Map([...list].filter(([, v]) => v === true));

  // Hooks
  const dispatch = useAppDispatch();

  // Listeners
  const handleChange = (values: string[]) => {
    const payload = connectionOptions.filter((option) =>
      values.includes(option.human_readable),
    );
    dispatch(setConnectionType(payload.map((obj) => obj.identifier)));
  };

  return (
    <MultiSelectDropdown
      label="Connection Type"
      list={list}
      onChange={handleChange}
      selectedList={selectedList}
      tooltipDisabled
      width={width}
    />
  );
};

export default ConnectionTypeFilter;
