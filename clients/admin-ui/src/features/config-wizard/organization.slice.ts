import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";
import { HYDRATE } from "next-redux-wrapper";

import type { AppState } from "../../app/store";
import {
  Organization,
  OrganizationParams,
  OrganizationResponse,
} from "./types";

export interface State {
  page: number;
  size: number;
  token: string | null;
}

const initialState: State = {
  page: 1,
  size: 25,
  token: null,
};

// Helpers
export const mapFiltersToSearchParams = ({
  page,
  size,
}: Partial<OrganizationParams>) => ({
  ...(page ? { page: `${page}` } : {}),
  ...(typeof size !== "undefined" ? { size: `${size}` } : {}),
});

// Organization API
export const organizationApi = createApi({
  reducerPath: "organizationApi",
  baseQuery: fetchBaseQuery({
    baseUrl: process.env.NEXT_PUBLIC_FIDESCTL_API,
    prepareHeaders: (headers, { getState }) => {
      const { token } = (getState() as AppState).user;
      headers.set("Access-Control-Allow-Origin", "*");
      if (token) {
        headers.set("authorization", `Bearer ${token}`);
      }
      return headers;
    },
  }),
  tagTypes: ["Organization"],
  endpoints: (build) => ({
    createOrganization: build.mutation<
      OrganizationResponse,
      Partial<Organization>
    >({
      query: (body) => ({
        url: `organization/`,
        method: "POST",
        body,
      }),
      invalidatesTags: () => ["Organization"],
    }),
    getOrganizationByFidesKey: build.query<object, string>({
      query: (fides_key) => ({ url: `organization/${fides_key}/` }),
      providesTags: ["Organization"],
    }),
    updateOrganization: build.mutation<
      Organization,
      Partial<Organization> & Pick<Organization, "fides_key">
    >({
      query: ({ ...patch }) => ({
        url: `organization/`,
        method: "PUT",
        body: patch,
      }),
      invalidatesTags: ["Organization"],
      // For optimistic updates
      async onQueryStarted(
        { fides_key, ...patch },
        { dispatch, queryFulfilled }
      ) {
        const patchResult = dispatch(
          // @ts-ignore
          organizationApi.util.updateQueryData(
            "getOrganizationByFidesKey",
            fides_key,
            (draft) => {
              Object.assign(draft, patch);
            }
          )
        );
        try {
          await queryFulfilled;
        } catch {
          patchResult.undo();
          /**
           * Alternatively, on failure you can invalidate the corresponding cache tags
           * to trigger a re-fetch:
           * dispatch(api.util.invalidateTags(['Organization']))
           */
        }
      },
    }),
  }),
});

export const {
  useGetOrganizationByFidesKeyQuery,
  useCreateOrganizationMutation,
  useUpdateOrganizationMutation,
} = organizationApi;

export const organizationSlice = createSlice({
  name: "organization",
  initialState,
  reducers: {
    assignToken: (state, action: PayloadAction<string>) => ({
      ...state,
      token: action.payload,
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
  },
  extraReducers: {
    [HYDRATE]: (state, action) => ({
      ...state,
      ...action.payload.user,
    }),
  },
});

export const { assignToken, setPage } = organizationSlice.actions;

// export const selectUserFilters = (state: AppState): OrganizationParams => ({
//   page: state.user.page,
//   size: state.user.size,
// });

export const { reducer } = organizationSlice;
