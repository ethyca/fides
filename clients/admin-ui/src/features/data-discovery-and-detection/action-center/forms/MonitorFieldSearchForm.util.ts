import {
  parseAsArrayOf,
  parseAsString,
  parseAsStringLiteral,
  UseQueryStatesKeysMap,
  Values,
} from "nuqs";
import * as v from "valibot";

import { ConfidenceBucket } from "~/types/api/models/ConfidenceBucket";

import {
  DEFAULT_FILTER_STATUSES,
  RESOURCE_STATUS,
} from "../fields/MonitorFields.const";

export const MonitorFieldSearchFormQuerySchema = v.object({
  search: v.nullish(v.string(), null),
  resource_status: v.nullish(
    v.array(v.picklist(RESOURCE_STATUS)),
    DEFAULT_FILTER_STATUSES,
  ),
  confidence_bucket: v.nullish(v.array(v.enum(ConfidenceBucket)), null),
  data_category: v.nullish(v.array(v.string()), null),
});

export const MonitorFieldSearchFormQueryState = {
  search: parseAsString,
  resource_status: parseAsArrayOf(
    parseAsStringLiteral(RESOURCE_STATUS),
  ).withDefault(DEFAULT_FILTER_STATUSES),
  confidence_bucket: parseAsArrayOf(
    parseAsStringLiteral(Object.values(ConfidenceBucket)),
  ),
  data_category: parseAsArrayOf(parseAsString),
} satisfies UseQueryStatesKeysMap;

export type MonitorFieldSearchForm =
  v.InferOutput<typeof MonitorFieldSearchFormQuerySchema> extends Values<
    typeof MonitorFieldSearchFormQueryState
  >
    ? v.InferOutput<typeof MonitorFieldSearchFormQuerySchema>
    : never;
