import { createSlice, PayloadAction } from "@reduxjs/toolkit";

import { baseApi } from "~/features/common/api.slice";
import {
  ActionType,
  BulkPostPrivacyRequests,
  fides__api__schemas__privacy_center_config__PrivacyCenterConfig as PrivacyCenterConfig,
  PrivacyRequestAccessResults,
  PrivacyRequestCreate,
  PrivacyRequestNotificationInfo,
  PrivacyRequestStatus,
} from "~/types/api";
import { PrivacyRequestSource } from "~/types/api/models/PrivacyRequestSource";

import type { RootState } from "../../app/store";
import { BASE_URL } from "../../constants";
import {
  ConfigStorageDetailsRequest,
  ConfigStorageSecretsDetailsRequest,
  DenyPrivacyRequest,
  GetUploadedManualWebhookDataRequest,
  PatchUploadManualWebhookDataRequest,
  PrivacyRequestEntity,
  PrivacyRequestParams,
  PrivacyRequestResponse,
  RetryRequests,
} from "./types";

// Helpers
export function mapFiltersToSearchParams({
  status,
  action_type,
  id,
  fuzzy_search_str,
  from,
  to,
  page,
  size,
  verbose,
  sort_direction,
  sort_field,
}: Partial<PrivacyRequestParams>): URLSearchParams {
  let fromISO: Date | undefined;
  if (from) {
    fromISO = new Date(from);
    fromISO.setUTCHours(0, 0, 0);
  }

  let toISO: Date | undefined;
  if (to) {
    toISO = new Date(to);
    toISO.setUTCHours(23, 59, 59);
  }

  const params = new URLSearchParams();

  params.set("include_identities", "true");
  params.set("include_custom_privacy_request_fields", "true");

  if (Array.isArray(action_type) && action_type.length > 0) {
    action_type.forEach((value) => {
      params.append("action_type", String(value));
    });
  }

  if (Array.isArray(status) && status.length > 0) {
    status.forEach((value) => {
      params.append("status", String(value));
    });
  }

  if (id) {
    params.set("request_id", id);
  }

  if (fuzzy_search_str) {
    params.set("fuzzy_search_str", fuzzy_search_str);
  }

  if (fromISO && !Number.isNaN(fromISO.getTime())) {
    params.set("created_gt", fromISO.toISOString());
  }
  if (toISO && !Number.isNaN(toISO.getTime())) {
    params.set("created_lt", toISO.toISOString());
  }

  if (page) {
    params.set("page", `${page}`);
  }

  if (typeof size !== "undefined") {
    params.set("size", `${size}`);
  }

  if (typeof verbose !== "undefined") {
    params.set("verbose", String(verbose));
  }

  if (sort_direction) {
    params.set("sort_direction", sort_direction);
  }

  if (sort_field) {
    params.set("sort_field", sort_field);
  }

  return params;
}

export const requestCSVDownload = async ({
  id,
  from,
  to,
  status,
  action_type,
  token,
}: PrivacyRequestParams & { token: string | null }) => {
  if (!token) {
    return null;
  }

  const params = mapFiltersToSearchParams({
    id,
    from,
    to,
    status,
    action_type,
  });
  params.set("download_csv", "true");

  return fetch(`${BASE_URL}/privacy-request?${params.toString()}`, {
    headers: {
      "Access-Control-Allow-Origin": "*",
      Authorization: `Bearer ${token}`,
      "X-Fides-Source": "fidesops-admin-ui",
    },
  })
    .then(async (response) => {
      if (!response.ok) {
        if (response.status === 400) {
          const errorData = await response.json();
          throw new Error(errorData.detail || "Bad request error");
        }
        throw new Error("Got a bad response from the server");
      }
      return response.blob();
    })
    .then((data) => {
      const a = document.createElement("a");
      a.href = window.URL.createObjectURL(data);
      a.download = "privacy-requests.csv";
      a.click();
    })
    .catch((error) => Promise.reject(error));
};

export const selectPrivacyRequestFilters = (
  state: RootState,
): PrivacyRequestParams => ({
  action_type: state.subjectRequests.action_type,
  from: state.subjectRequests.from,
  id: state.subjectRequests.id,
  fuzzy_search_str: state.subjectRequests.fuzzy_search_str,
  page: state.subjectRequests.page,
  size: state.subjectRequests.size,
  sort_direction: state.subjectRequests.sort_direction,
  sort_field: state.subjectRequests.sort_field,
  status: state.subjectRequests.status,
  to: state.subjectRequests.to,
  verbose: state.subjectRequests.verbose,
});

export const selectRequestStatus = (state: RootState) =>
  state.subjectRequests.status;

export const selectRetryRequests = (state: RootState): RetryRequests => ({
  checkAll: state.subjectRequests.checkAll,
  errorRequests: state.subjectRequests.errorRequests,
});

// Subject requests state (filters, etc.)
type SubjectRequestsState = {
  action_type?: ActionType[];
  checkAll: boolean;
  errorRequests: string[];
  from: string;
  id: string;
  fuzzy_search_str?: string;
  page: number;
  size: number;
  sort_direction?: string;
  sort_field?: string;
  status?: PrivacyRequestStatus[];
  to: string;
  verbose?: boolean;
};

const initialState: SubjectRequestsState = {
  checkAll: false,
  errorRequests: [],
  from: "",
  id: "",
  page: 1,
  size: 25,
  to: "",
};

export const subjectRequestsSlice = createSlice({
  name: "subjectRequests",
  initialState,
  reducers: {
    clearAllFilters: () => ({
      ...initialState,
    }),
    clearSortKeys: (state) => ({
      ...state,
      sort_direction: undefined,
      sort_field: undefined,
    }),
    setPage: (state, action: PayloadAction<number>) => ({
      ...state,
      page: action.payload,
    }),
    setRequestFrom: (state, action: PayloadAction<string>) => ({
      ...state,
      page: initialState.page,
      from: action.payload,
    }),
    setRequestId: (state, action: PayloadAction<string>) => ({
      ...state,
      page: initialState.page,
      id: action.payload,
    }),
    setFuzzySearchStr: (state, action: PayloadAction<string>) => ({
      ...state,
      page: initialState.page,
      fuzzy_search_str: action.payload,
    }),
    setRequestStatus: (
      state,
      action: PayloadAction<PrivacyRequestStatus[]>,
    ) => ({
      ...state,
      page: initialState.page,
      status: action.payload,
    }),
    setRequestActionType: (state, action: PayloadAction<ActionType[]>) => ({
      ...state,
      page: initialState.page,
      action_type: action.payload,
    }),
    setRequestTo: (state, action: PayloadAction<string>) => ({
      ...state,
      page: initialState.page,
      to: action.payload,
    }),
    setRetryRequests: (state, action: PayloadAction<RetryRequests>) => ({
      ...state,
      checkAll: action.payload.checkAll,
      errorRequests: action.payload.errorRequests,
    }),
    setSortDirection: (state, action: PayloadAction<string>) => ({
      ...state,
      sort_direction: action.payload,
    }),
    setSortKey: (state, action: PayloadAction<string>) => ({
      ...state,
      sort_field: action.payload,
    }),
    setSize: (state, action: PayloadAction<number>) => ({
      ...state,
      page: initialState.page,
      size: action.payload,
    }),
    setVerbose: (state, action: PayloadAction<boolean>) => ({
      ...state,
      verbose: action.payload,
    }),
  },
});

export const {
  clearAllFilters,
  clearSortKeys,
  setPage,
  setRequestFrom,
  setRequestId,
  setRequestStatus,
  setRequestActionType,
  setRequestTo,
  setRetryRequests,
  setFuzzySearchStr,
  setSortDirection,
  setSortKey,
  setVerbose,
} = subjectRequestsSlice.actions;

export const { reducer } = subjectRequestsSlice;

// Privacy requests API
export const privacyRequestApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    approveRequest: build.mutation<
      PrivacyRequestEntity,
      Partial<PrivacyRequestEntity> & Pick<PrivacyRequestEntity, "id">
    >({
      query: ({ id }) => ({
        url: "privacy-request/administrate/approve",
        method: "PATCH",
        body: {
          request_ids: [id],
        },
      }),
      invalidatesTags: ["Request"],
    }),
    bulkRetry: build.mutation<BulkPostPrivacyRequests, string[]>({
      query: (values) => ({
        url: `privacy-request/bulk/retry`,
        method: "POST",
        body: values,
      }),
      invalidatesTags: ["Request"],
    }),
    denyRequest: build.mutation<PrivacyRequestEntity, DenyPrivacyRequest>({
      query: ({ id, reason }) => ({
        url: "privacy-request/administrate/deny",
        method: "PATCH",
        body: {
          request_ids: [id],
          reason,
        },
      }),
      invalidatesTags: ["Request"],
    }),
    softDeleteRequest: build.mutation<
      PrivacyRequestEntity,
      Partial<PrivacyRequestEntity> & Pick<PrivacyRequestEntity, "id">
    >({
      query: ({ id }) => ({
        url: `privacy-request/${id}/soft-delete`,
        method: "POST",
      }),
      invalidatesTags: ["Request"],
    }),
    getAllPrivacyRequests: build.query<
      PrivacyRequestResponse,
      Partial<PrivacyRequestParams>
    >({
      query: (filters) => ({
        url: `privacy-request?${mapFiltersToSearchParams(filters).toString()}`,
      }),
      providesTags: () => ["Request"],
      async onQueryStarted(_key, { dispatch, queryFulfilled }) {
        queryFulfilled.then(({ data }) => {
          const hasError = data.items.some((item) => item.status === "error");
          if (hasError) {
            dispatch(setRetryRequests({ checkAll: false, errorRequests: [] }));
          }
        });
      },
    }),
    postPrivacyRequest: build.mutation<
      PrivacyRequestResponse,
      PrivacyRequestCreate[]
    >({
      query: (payload) => ({
        url: `privacy-request/authenticated`,
        method: "POST",
        body: payload.map((item) => ({
          ...item,
          source: PrivacyRequestSource.REQUEST_MANAGER,
        })),
      }),
      invalidatesTags: () => ["Request"],
    }),
    getNotification: build.query<PrivacyRequestNotificationInfo, void>({
      // NOTE: This will intentionally return a 404 with `details` if the notification is not yet set.
      query: () => ({
        url: `privacy-request/notification`,
      }),
      providesTags: ["Notification"],
      transformResponse: (response: PrivacyRequestNotificationInfo) => {
        const cloneResponse = { ...response };
        if (cloneResponse.email_addresses?.length > 0) {
          cloneResponse.email_addresses = cloneResponse.email_addresses.filter(
            (item) => item !== "",
          );
        }
        return cloneResponse;
      },
    }),
    getUploadedManualAccessWebhookData: build.query<
      any,
      GetUploadedManualWebhookDataRequest
    >({
      query: (params) => ({
        url: `privacy-request/${params.privacy_request_id}/access_manual_webhook/${params.connection_key}`,
      }),
    }),
    getUploadedManualErasureWebhookData: build.query<
      any,
      GetUploadedManualWebhookDataRequest
    >({
      query: (params) => ({
        url: `privacy-request/${params.privacy_request_id}/erasure_manual_webhook/${params.connection_key}`,
      }),
    }),
    resumePrivacyRequestFromRequiresInput: build.mutation<any, string>({
      query: (privacy_request_id) => ({
        url: `privacy-request/${privacy_request_id}/resume_from_requires_input`,
        method: "POST",
      }),
      invalidatesTags: ["Request"],
    }),
    retry: build.mutation<
      PrivacyRequestEntity,
      Pick<PrivacyRequestEntity, "id">
    >({
      query: ({ id }) => ({
        url: `privacy-request/${id}/retry`,
        method: "POST",
      }),
      invalidatesTags: ["Request"],
    }),
    saveNotification: build.mutation<any, PrivacyRequestNotificationInfo>({
      query: (params) => ({
        url: `privacy-request/notification`,
        method: "PUT",
        body: params,
      }),
      invalidatesTags: ["Notification"],
    }),
    getActiveStorage: build.query<any, void>({
      query: () => ({
        url: `storage/default/active`,
      }),
    }),
    getStorageDetails: build.query<any, ConfigStorageDetailsRequest>({
      query: (params) => ({
        url: `storage/default/${params.type}`,
      }),
    }),
    createStorage: build.mutation<any, ConfigStorageDetailsRequest>({
      query: (params) => ({
        url: `storage/default`,
        method: "PUT",
        body: params,
      }),
    }),
    createStorageSecrets: build.mutation<
      ConfigStorageDetailsRequest,
      ConfigStorageSecretsDetailsRequest
    >({
      query: (params) => ({
        url: `storage/default/${params.type}/secret`,
        method: "PUT",
        body: params.details,
      }),
    }),
    uploadManualAccessWebhookData: build.mutation<
      any,
      PatchUploadManualWebhookDataRequest
    >({
      query: (params) => ({
        url: `privacy-request/${params.privacy_request_id}/access_manual_webhook/${params.connection_key}`,
        method: "PATCH",
        body: params.body,
      }),
    }),
    uploadManualErasureWebhookData: build.mutation<
      any,
      PatchUploadManualWebhookDataRequest
    >({
      query: (params) => ({
        url: `privacy-request/${params.privacy_request_id}/erasure_manual_webhook/${params.connection_key}`,
        method: "PATCH",
        body: params.body,
      }),
    }),
    getPrivacyCenterConfig: build.query<PrivacyCenterConfig, void>({
      query: () => ({
        method: "GET",
        url: `plus/privacy-center-config`,
      }),
    }),
    getPrivacyRequestAccessResults: build.query<
      PrivacyRequestAccessResults,
      { privacy_request_id: string }
    >({
      query: ({ privacy_request_id }) => ({
        method: "GET",
        url: `privacy-request/${privacy_request_id}/access-results`,
      }),
    }),
    getFilteredResults: build.query<
      {
        privacy_request_id: string;
        status: PrivacyRequestStatus;
        results: {
          [key: string]: Array<Record<string, any>>;
        };
      },
      { privacy_request_id: string }
    >({
      query: ({ privacy_request_id }) => ({
        method: "GET",
        url: `privacy-request/${privacy_request_id}/filtered-results`,
      }),
    }),
    getTestLogs: build.query<
      Array<{
        timestamp: string;
        level: string;
        module_info: string;
        message: string;
      }>,
      { privacy_request_id: string }
    >({
      query: ({ privacy_request_id }) => ({
        method: "GET",
        url: `privacy-request/${privacy_request_id}/logs`,
      }),
    }),
    postPrivacyRequestFinalize: build.mutation({
      query: ({ privacyRequestId }: { privacyRequestId: string }) => ({
        method: "POST",
        url: `/privacy-request/${privacyRequestId}/finalize`,
      }),
      invalidatesTags: ["Request"],
    }),
  }),
});

export const {
  useApproveRequestMutation,
  useBulkRetryMutation,
  useDenyRequestMutation,
  useSoftDeleteRequestMutation,
  useGetAllPrivacyRequestsQuery,
  usePostPrivacyRequestMutation,
  useGetNotificationQuery,
  useResumePrivacyRequestFromRequiresInputMutation,
  useRetryMutation,
  useSaveNotificationMutation,
  useUploadManualAccessWebhookDataMutation,
  useUploadManualErasureWebhookDataMutation,
  useGetPrivacyCenterConfigQuery,
  useGetStorageDetailsQuery,
  useCreateStorageMutation,
  useCreateStorageSecretsMutation,
  useGetActiveStorageQuery,
  useGetPrivacyRequestAccessResultsQuery,
  useGetFilteredResultsQuery,
  useGetTestLogsQuery,
  usePostPrivacyRequestFinalizeMutation,
} = privacyRequestApi;
