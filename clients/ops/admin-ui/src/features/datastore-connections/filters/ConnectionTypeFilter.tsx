import MultiSelectDropdown from "common/dropdown/MultiSelectDropdown";
import { capitalize } from "common/utils";
import React, { useCallback, useMemo } from "react";
import { useDispatch, useSelector } from "react-redux";

import { ConnectionType } from "../constants";
import {
  selectDatastoreConnectionFilters,
  setConnectionType,
} from "../datastore-connection.slice";

export type ConnectionTypeFilterProps = {
  width?: string;
};

const ConnectionTypeFilter: React.FC<ConnectionTypeFilterProps> = ({
  width,
}) => {
  // eslint-disable-next-line @typescript-eslint/naming-convention
  const { connection_type } = useSelector(selectDatastoreConnectionFilters);

  const loadList = useCallback((): Map<string, boolean> => {
    const list = new Map<string, boolean>();
    const valuesList = Object.values(ConnectionType).sort();
    valuesList.forEach((value) => {
      let result = false;
      if (connection_type?.includes(value)) {
        result = true;
      }
      list.set(capitalize(value), result);
    });
    return list;
  }, [connection_type]);

  const list = useMemo(() => loadList(), [loadList]);
  const selectedList = new Map([...list].filter(([, v]) => v === true));

  // Hooks
  const dispatch = useDispatch();

  // Listeners
  const handleChange = (values: string[]) => {
    const payload = values.map(
      (value) => value.toLowerCase() as ConnectionType
    );
    dispatch(setConnectionType(payload));
  };

  return (
    <MultiSelectDropdown
      label="Datastore Type"
      list={list}
      onChange={handleChange}
      selectedList={selectedList}
      tooltipDisabled
      width={width}
    />
  );
};

export default ConnectionTypeFilter;
