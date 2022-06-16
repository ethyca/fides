import { createSlice } from "@reduxjs/toolkit";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";
import { HYDRATE } from "next-redux-wrapper";
import { Organization, OrganizationResponse } from "./types";

// Organization API
export const organizationApi = createApi({
  reducerPath: "organizationApi",
  baseQuery: fetchBaseQuery({
    baseUrl: process.env.NEXT_PUBLIC_FIDESCTL_API,
    prepareHeaders: (headers) => headers,
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
    getOrganizationByFidesKey: build.query<Partial<Organization>, string>({
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
  initialState: {},
  reducers: {},
  extraReducers: {
    [HYDRATE]: (state, action) => ({
      ...state,
      ...action.payload.user,
    }),
  },
});

export const { reducer } = organizationSlice;
