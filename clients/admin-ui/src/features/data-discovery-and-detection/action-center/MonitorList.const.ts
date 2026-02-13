import { parseAsString, parseAsStringEnum, UseQueryStatesKeysMap } from "nuqs";

import { MONITOR_TYPES } from "./utils/getMonitorType";

export const SearchFormQueryState = (
  availableMonitors: Array<MONITOR_TYPES>,
  id?: string,
) =>
  ({
    search: parseAsString.withDefault(""),
    monitor_type: parseAsStringEnum(availableMonitors),
    steward_key: id
      ? parseAsString.withDefault(id).withOptions({
          clearOnDefault: false,
        })
      : parseAsString,
  }) satisfies UseQueryStatesKeysMap;
