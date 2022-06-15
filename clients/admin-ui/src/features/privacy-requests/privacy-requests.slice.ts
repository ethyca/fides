import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import type { RootState } from "../../app/store";
import { BASE_API_URN } from "../../constants";
import { selectToken } from "../auth";
import {
  DenyPrivacyRequest,
  PrivacyRequest,
  PrivacyRequestParams,
  PrivacyRequestResponse,
  PrivacyRequestStatus,
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
    ...(status ? { status } : {}),
    ...(id ? { request_id: id } : {}),
    ...(fromISO ? { created_gt: fromISO.toISOString() } : {}),
    ...(toISO ? { created_lt: toISO.toISOString() } : {}),
    ...(page ? { page: `${page}` } : {}),
    ...(typeof size !== "undefined" ? { size: `${size}` } : {}),
    ...(verbose ? { verbose } : {}),
  };
}

// Subject requests API
export const privacyRequestApi = createApi({
  reducerPath: "privacyRequestApi",
  baseQuery: fetchBaseQuery({
    baseUrl: BASE_API_URN,
    prepareHeaders: (headers, { getState }) => {
      const token = selectToken(getState() as RootState);
      headers.set("Access-Control-Allow-Origin", "*");
      if (token) {
        headers.set("authorization", `Bearer ${token}`);
      }
      return headers;
    },
  }),
  tagTypes: ["Request"],
  endpoints: (build) => ({
    getAllPrivacyRequests: build.query<
      PrivacyRequestResponse,
      Partial<PrivacyRequestParams>
    >({
      query: (filters) => ({
        url: `privacy-request`,
        params: mapFiltersToSearchParams(filters),
      }),
      providesTags: () => ["Request"],
    }),
    approveRequest: build.mutation<
      PrivacyRequest,
      Partial<PrivacyRequest> & Pick<PrivacyRequest, "id">
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
    denyRequest: build.mutation<PrivacyRequest, DenyPrivacyRequest>({
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
  }),
});

export const {
  useGetAllPrivacyRequestsQuery,
  useApproveRequestMutation,
  useDenyRequestMutation,
} = privacyRequestApi;

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
    `${BASE_API_URN}/privacy-request?${new URLSearchParams({
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

// Subject requests state (filters, etc.)
interface SubjectRequestsState {
  revealPII: boolean;
  status?: PrivacyRequestStatus;
  id: string;
  from: string;
  to: string;
  page: number;
  size: number;
  verbose?: boolean;
}

const initialState: SubjectRequestsState = {
  revealPII: false,
  id: "",
  from: "",
  to: "",
  page: 1,
  size: 25,
};

export const subjectRequestsSlice = createSlice({
  name: "subjectRequests",
  initialState,
  reducers: {
    setRevealPII: (state, action: PayloadAction<boolean>) => ({
      ...state,
      revealPII: action.payload,
    }),
    setRequestStatus: (state, action: PayloadAction<PrivacyRequestStatus>) => ({
      ...state,
      page: initialState.page,
      status: action.payload,
    }),
    setRequestId: (state, action: PayloadAction<string>) => ({
      ...state,
      page: initialState.page,
      id: action.payload,
    }),
    setRequestFrom: (state, action: PayloadAction<string>) => ({
      ...state,
      page: initialState.page,
      from: action.payload,
    }),
    setRequestTo: (state, action: PayloadAction<string>) => ({
      ...state,
      page: initialState.page,
      to: action.payload,
    }),
    clearAllFilters: ({ revealPII }) => ({
      ...initialState,
      revealPII,
    }),
    setPage: (state, action: PayloadAction<number>) => ({
      ...state,
      page: action.payload,
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
  setRevealPII,
  setRequestId,
  setRequestStatus,
  setRequestFrom,
  setRequestTo,
  setPage,
  setVerbose,
  clearAllFilters,
} = subjectRequestsSlice.actions;

export const selectRevealPII = (state: RootState) =>
  state.subjectRequests.revealPII;
export const selectRequestStatus = (state: RootState) =>
  state.subjectRequests.status;

export const selectPrivacyRequestFilters = (
  state: RootState
): PrivacyRequestParams => ({
  status: state.subjectRequests.status,
  id: state.subjectRequests.id,
  from: state.subjectRequests.from,
  to: state.subjectRequests.to,
  page: state.subjectRequests.page,
  size: state.subjectRequests.size,
  verbose: state.subjectRequests.verbose,
});

export const { reducer } = subjectRequestsSlice;
