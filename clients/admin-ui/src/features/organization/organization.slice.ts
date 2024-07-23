import { createSlice } from "@reduxjs/toolkit";

import { baseApi } from "~/features/common/api.slice";
import { Organization } from "~/types/api";

// Organization API
const organizationApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    createOrganization: build.mutation<Organization, Partial<Organization>>({
      query: (body) => ({
        url: `organization`,
        method: "POST",
        body,
      }),
      invalidatesTags: () => ["Organization"],
    }),
    getOrganizationByFidesKey: build.query<
      Partial<Organization> & Pick<Organization, "fides_key">,
      string
    >({
      query: (fides_key) => ({ url: `organization/${fides_key}` }),
      providesTags: ["Organization"],
    }),
    updateOrganization: build.mutation<
      Organization,
      Partial<Organization> & Pick<Organization, "fides_key">
    >({
      query: ({ ...patch }) => ({
        url: `organization`,
        method: "PUT",
        body: patch,
      }),
      invalidatesTags: ["Organization"],
      // For optimistic updates
      async onQueryStarted(
        { fides_key, ...patch },
        { dispatch, queryFulfilled },
      ) {
        const patchResult = dispatch(
          organizationApi.util.updateQueryData(
            "getOrganizationByFidesKey",
            fides_key,
            (draft) => {
              Object.assign(draft, patch);
            },
          ),
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
});

export const { reducer } = organizationSlice;
