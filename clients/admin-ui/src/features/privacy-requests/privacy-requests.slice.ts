import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";
import { addCommonHeaders } from "common/CommonHeaders";

import {
  BulkPostPrivacyRequests,
  PrivacyRequestNotificationInfo,
} from "~/types/api";

import type { RootState } from "../../app/store";
import { BASE_URL } from "../../constants";
import { selectToken } from "../auth";
import {
  DenyPrivacyRequest,
  GetUpdloadedManualWebhookDataRequest,
  PatchUploadManualWebhookDataRequest,
  PrivacyRequestEntity,
  PrivacyRequestParams,
  PrivacyRequestResponse,
  PrivacyRequestStatus,
  RetryRequests,
} from "./types";

// Helpers
export function mapFiltersToSearchParams({
  status,
  id,
  from,
  to,
  page,
  size,
  verbose,
  sort_direction,
  sort_field,
}: Partial<PrivacyRequestParams>): any {
  let fromISO;
  if (from) {
    fromISO = new Date(from);
    fromISO.setUTCHours(0, 0, 0);
  }

  let toISO;
  if (to) {
    toISO = new Date(to);
    toISO.setUTCHours(23, 59, 59);
  }

  return {
    include_identities: "true",
    ...(status && status.length > 0 ? { status: status.join("&status=") } : {}),
    ...(id ? { request_id: id } : {}),
    ...(fromISO ? { created_gt: fromISO.toISOString() } : {}),
    ...(toISO ? { created_lt: toISO.toISOString() } : {}),
    ...(page ? { page: `${page}` } : {}),
    ...(typeof size !== "undefined" ? { size: `${size}` } : {}),
    ...(verbose ? { verbose } : {}),
    ...(sort_direction ? { sort_direction } : {}),
    ...(sort_field ? { sort_field } : {}),
  };
}

export const requestCSVDownload = async ({
  id,
  from,
  to,
  status,
  token,
}: PrivacyRequestParams & { token: string | null }) => {
  if (!token) {
    return null;
  }

  return fetch(
    `${BASE_URL}/privacy-request?${new URLSearchParams({
      ...mapFiltersToSearchParams({
        id,
        from,
        to,
        status,
      }),
      download_csv: "true",
    })}`,
    {
      headers: {
        "Access-Control-Allow-Origin": "*",
        Authorization: `Bearer ${token}`,
        "X-Fides-Source": "fidesops-admin-ui",
      },
    }
  )
    .then((response) => {
      if (!response.ok) {
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
  state: RootState
): PrivacyRequestParams => ({
  from: state.subjectRequests.from,
  id: state.subjectRequests.id,
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

export const selectRevealPII = (state: RootState) =>
  state.subjectRequests.revealPII;

// Subject requests state (filters, etc.)
type SubjectRequestsState = {
  checkAll: boolean;
  errorRequests: string[];
  from: string;
  id: string;
  page: number;
  revealPII: boolean;
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
  revealPII: false,
  size: 25,
  to: "",
};

export const subjectRequestsSlice = createSlice({
  name: "subjectRequests",
  initialState,
  reducers: {
    clearAllFilters: ({ revealPII }) => ({
      ...initialState,
      revealPII,
    }),
    clearSortFields: (state) => ({
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
    setRequestStatus: (
      state,
      action: PayloadAction<PrivacyRequestStatus[]>
    ) => ({
      ...state,
      page: initialState.page,
      status: action.payload,
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
    setRevealPII: (state, action: PayloadAction<boolean>) => ({
      ...state,
      revealPII: action.payload,
    }),
    setSortDirection: (state, action: PayloadAction<string>) => ({
      ...state,
      sort_direction: action.payload,
    }),
    setSortField: (state, action: PayloadAction<string>) => ({
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
  clearSortFields,
  setPage,
  setRequestFrom,
  setRequestId,
  setRequestStatus,
  setRequestTo,
  setRetryRequests,
  setRevealPII,
  setSortDirection,
  setSortField,
  setVerbose,
} = subjectRequestsSlice.actions;

export const { reducer } = subjectRequestsSlice;

// Privacy requests API
export const privacyRequestApi = createApi({
  reducerPath: "privacyRequestApi",
  baseQuery: fetchBaseQuery({
    baseUrl: BASE_URL,
    prepareHeaders: (headers, { getState }) => {
      const token: string | null = selectToken(getState() as RootState);
      addCommonHeaders(headers, token);
      return headers;
    },
  }),
  tagTypes: ["Request", "Notification"],
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
    getAllPrivacyRequests: build.query<
      PrivacyRequestResponse,
      Partial<PrivacyRequestParams>
    >({
      query: (filters) => ({
        url: `privacy-request?${decodeURIComponent(
          new URLSearchParams(mapFiltersToSearchParams(filters)).toString()
        )}`,
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
    getNotification: build.query<PrivacyRequestNotificationInfo, void>({
      query: () => ({
        url: `privacy-request/notification`,
      }),
      providesTags: ["Notification"],
      transformResponse: (response: PrivacyRequestNotificationInfo) => {
        const cloneResponse = { ...response };
        if (cloneResponse.email_addresses?.length > 0) {
          cloneResponse.email_addresses = cloneResponse.email_addresses.filter(
            (item) => item !== ""
          );
        }
        return cloneResponse;
      },
    }),
    getUploadedManualWebhookData: build.query<
      any,
      GetUpdloadedManualWebhookDataRequest
    >({
      query: (params) => ({
        url: `privacy-request/${params.privacy_request_id}/access_manual_webhook/${params.connection_key}`,
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
    getStorageDetails: build.query<any, any>({
      query: (params) => ({
        url: `storage/default/${params.storage_type}`,
      }),
    }),
    createActiveStorage: build.mutation<any, any>({
      query: (params) => ({
        url: `application/settings`,
        method: "PUT",
        body: params,
      }),
    }),
    createStorage: build.mutation<any, any>({
      query: (params) => ({
        url: `storage/default`,
        method: "PUT",
        body: params,
      }),
    }),
    createStorageSecrets: build.mutation<any, any>({
      query: (params) => ({
        url: `storage/default/${params.storage_type}/secret`,
        method: "PUT",
        body: params,
      }),
    }),
    getMessagingConfigurationDetails: build.query<any, any>({
      query: (params) => ({
        url: `messaging/config/${params.config_key}`,
      }),
    }),
    createMessagingConfiguration: build.mutation<any, any>({
      query: (params) => ({
        url: `messaging/config`,
        method: "PUT",
        body: params,
      }),
    }),
    updateMessagingConfiguration: build.mutation<any, any>({
      query: (params) => ({
        url: `messaging/config/${params.config_key}`,
        method: "PATCH",
        body: params,
      }),
    }),
    createMessagingConfigurationSecrets: build.mutation<any, any>({
      query: (params) => ({
        url: `messaging/config/${params.config_key}/secret`,
        method: "PUT",
        body: params,
      }),
    }),
    uploadManualWebhookData: build.mutation<
      any,
      PatchUploadManualWebhookDataRequest
    >({
      query: (params) => ({
        url: `privacy-request/${params.privacy_request_id}/access_manual_webhook/${params.connection_key}`,
        method: "PATCH",
        body: params.body,
      }),
    }),
  }),
});

export const {
  useApproveRequestMutation,
  useBulkRetryMutation,
  useDenyRequestMutation,
  useGetAllPrivacyRequestsQuery,
  useGetNotificationQuery,
  useGetUploadedManualWebhookDataQuery,
  useResumePrivacyRequestFromRequiresInputMutation,
  useRetryMutation,
  useSaveNotificationMutation,
  useUploadManualWebhookDataMutation,
  useGetStorageDetailsQuery,
  useCreateStorageMutation,
  useCreateStorageSecretsMutation,
  useGetMessagingConfigurationDetailsQuery,
  useCreateActiveStorageMutation,
  useCreateMessagingConfigurationMutation,
  useUpdateMessagingConfigurationMutation,
  useCreateMessagingConfigurationSecretsMutation,
} = privacyRequestApi;
