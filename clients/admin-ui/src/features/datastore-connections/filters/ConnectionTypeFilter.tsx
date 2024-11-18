import { useCallback, useMemo } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { FilterSelect } from "~/features/common/dropdown/FilterSelect";
import { selectConnectionTypeState } from "~/features/connection-type";

import {
  selectDatastoreConnectionFilters,
  setConnectionType,
} from "../datastore-connection.slice";

const ConnectionTypeFilter = () => {
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
  const options = [...list].map(([key]) => ({ value: key }));

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
    <FilterSelect
      mode="multiple"
      placeholder="Connection Type"
      options={options}
      onChange={handleChange}
      defaultValue={connection_type?.length ? connection_type : []}
      className="w-60"
    />
  );
};

export default ConnectionTypeFilter;
