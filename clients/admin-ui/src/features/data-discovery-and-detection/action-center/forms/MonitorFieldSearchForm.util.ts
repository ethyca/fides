import {
  parseAsArrayOf,
  parseAsString,
  parseAsStringLiteral,
  UseQueryStatesKeysMap,
  Values,
} from "nuqs";
import * as v from "valibot";

import { ConfidenceBucket } from "~/types/api/models/ConfidenceBucket";

import { RESOURCE_STATUS } from "../fields/MonitorFields.const";

export const MonitorFieldSearchFormQuerySchema = v.object({
  search: v.nullable(v.string(), null),
  resource_status: v.nullable(v.array(v.picklist(RESOURCE_STATUS))),
  confidence_bucket: v.nullable(v.array(v.enum(ConfidenceBucket)), null),
  data_category: v.nullable(v.array(v.string()), null),
});

export const MonitorFieldSearchFormQueryState = {
  search: parseAsString,
  resource_status: parseAsArrayOf(parseAsStringLiteral(RESOURCE_STATUS)),
  confidence_bucket: parseAsArrayOf(
    parseAsStringLiteral(Object.values(ConfidenceBucket)),
  ),
  data_category: parseAsArrayOf(parseAsString),
} satisfies UseQueryStatesKeysMap;

/**
 ** This type returns the resulting type from the valibot schema defined above if it's type signature matches the output of the state defined by nuqs.
 ** If they types do not match, it returns never, causing an error
 * */
export type MonitorFieldSearchForm =
  v.InferOutput<typeof MonitorFieldSearchFormQuerySchema> extends Values<
    typeof MonitorFieldSearchFormQueryState
  >
    ? v.InferOutput<typeof MonitorFieldSearchFormQuerySchema>
    : never;
