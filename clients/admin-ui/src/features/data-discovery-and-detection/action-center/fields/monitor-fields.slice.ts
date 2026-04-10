import { baseApi } from "~/features/common/api.slice";
import { buildArrayQueryParams } from "~/features/common/utils";
import { AllowedActionsResponse } from "~/types/api/models/AllowedActionsResponse";
import { FilteredFieldActionRequest } from "~/types/api/models/FilteredFieldActionRequest";
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
          search_regex,
          diff_status,
          confidence_bucket,
          ...arrayQueryParams
        },
      }) => {
        const queryParams = buildArrayQueryParams({
          ...arrayQueryParams,
          ...(search ? { search: [search] } : {}),
          ...(diff_status ? { diff_status } : {}),
          ...(confidence_bucket ? { confidence_bucket } : {}),
        });
        return {
          url: `/plus/discovery-monitor/${monitor_config_id}/fields?${queryParams?.toString()}`,
          params: {
            page,
            size,
            ...(search_regex ? { search_regex: true } : {}),
          },
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
        body: {
          excluded_resource_urns: string[];
        };
      }
    >({
      query: ({
        path: { monitor_config_id, action_type },
        query: {
          search,
          search_regex,
          diff_status,
          confidence_bucket,
          ...arrayQueryParams
        },
        body,
      }) => {
        const queryParams = buildArrayQueryParams({
          ...arrayQueryParams,
          ...(search ? { search: [search] } : {}),
          ...(diff_status ? { diff_status } : {}),
          ...(confidence_bucket ? { confidence_bucket } : {}),
        });
        return {
          url: `/plus/discovery-monitor/${monitor_config_id}/fields/${action_type}?${queryParams.toString()}`,
          method: "POST",
          body,
          params: {
            ...(search_regex ? { search_regex: true } : {}),
          },
        };
      },
      invalidatesTags: [
        "Monitor Field Results",
        "Monitor Field Details",
        "Discovery Monitor Results",
      ],
    }),
    getAllowedActions: build.query<
      AllowedActionsResponse,
      MonitorFieldParameters & {
        body: FilteredFieldActionRequest;
      }
    >({
      query: ({
        path: { monitor_config_id },
        query: {
          search,
          search_regex,
          diff_status,
          confidence_bucket,
          ...arrayQueryParams
        },
        body,
      }) => {
        const queryParams = buildArrayQueryParams({
          ...arrayQueryParams,
          ...(search ? { search: [search] } : {}),
          ...(diff_status ? { diff_status } : {}),
          ...(confidence_bucket ? { confidence_bucket } : {}),
        });

        return {
          url: `/plus/discovery-monitor/${monitor_config_id}/fields/allowed-actions?${queryParams.toString()}`,
          method: "POST",
          body,
          params: {
            ...(search_regex ? { search_regex: true } : {}),
          },
        };
      },
      providesTags: ["Allowed Monitor Field Actions"],
    }),
  }),
});

export const {
  useFieldActionsMutation,
  useGetMonitorFieldsQuery,
  useLazyGetAllowedActionsQuery,
  util: monitorFieldUtil,
} = monitorFieldApi;
