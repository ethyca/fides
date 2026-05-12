import {
  parseAsString,
  parseAsStringEnum,
  UseQueryStatesKeysMap,
  Values,
} from "nuqs";
import * as v from "valibot";

import { APIMonitorType } from "~/types/api/models/APIMonitorType";

export const MonitorSearchFormQuerySchema = (
  availableMonitors: Array<APIMonitorType>,
) =>
  v.object({
    search: v.nullish(v.string(), null),
    monitor_type: v.nullish(v.picklist(availableMonitors), null),
    steward_key: v.nullish(v.string(), null),
  });

export const SearchFormQueryState = (
  availableMonitors: Array<APIMonitorType>,
  id?: string,
) =>
  ({
    search: parseAsString,
    monitor_type: parseAsStringEnum(availableMonitors),
    steward_key: id
      ? parseAsString.withDefault(id).withOptions({
          clearOnDefault: false,
        })
      : parseAsString,
  }) satisfies UseQueryStatesKeysMap;

export type MonitorSearchForm =
  v.InferOutput<ReturnType<typeof MonitorSearchFormQuerySchema>> extends Values<
    ReturnType<typeof SearchFormQueryState>
  >
    ? v.InferOutput<ReturnType<typeof MonitorSearchFormQuerySchema>>
    : never;
