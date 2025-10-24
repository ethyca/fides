import { baseApi } from "~/features/common/api.slice";
import { buildArrayQueryParams } from "~/features/common/utils";
import { MonitorActionResponse } from "~/types/api/models/MonitorActionResponse";
import { Page_DatastoreStagedResourceAPIResponse_ } from "~/types/api/models/Page_DatastoreStagedResourceAPIResponse_";
import { PaginationQueryParams } from "~/types/query-params";

import {
  FieldActionTypeValue,
  MonitorFieldParameters,
  MonitorFieldQueryParameters,
} from "./types";

const monitorFieldApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getMonitorFields: build.query<
      Page_DatastoreStagedResourceAPIResponse_,
      MonitorFieldParameters & {
        query: MonitorFieldQueryParameters & Partial<PaginationQueryParams>;
      }
    >({
      query: ({
        path: { monitor_config_id },
        query: {
          page = 1,
          size = 20,
          search,
          diff_status,
          confidence_score,
          ...arrayQueryParams
        },
      }) => {
        const queryParams = buildArrayQueryParams({
          ...arrayQueryParams,
          ...(search ? { search: [search] } : {}),
          ...(diff_status ? { diff_status } : {}),
          ...(confidence_score ? { confidence_score } : {}),
        });
        return {
          url: `/plus/discovery-monitor/${monitor_config_id}/fields?${queryParams?.toString()}`,
          params: { page, size },
        };
      },
      providesTags: ["Monitor Field Results"],
    }),
    fieldActions: build.mutation<
      MonitorActionResponse,
      MonitorFieldParameters & {
        path: MonitorFieldParameters["path"] & {
          action_type: FieldActionTypeValue;
        };
      }
    >({
      query: ({
        path: { monitor_config_id, action_type },
        query: { search, diff_status, confidence_score, ...arrayQueryParams },
        ...body
      }) => {
        const queryParams = buildArrayQueryParams({
          ...arrayQueryParams,
          ...(search ? { search: [search] } : {}),
          ...(diff_status ? { diff_status } : {}),
          ...(confidence_score ? { confidence_score } : {}),
        });

        return {
          url: `/plus/discovery-monitor/${monitor_config_id}/fields/${action_type}?${queryParams.toString()}`,
          method: "POST",
          body,
        };
      },
      invalidatesTags: ["Monitor Field Results"],
    }),
  }),
});

export const { useFieldActionsMutation, useGetMonitorFieldsQuery } =
  monitorFieldApi;
