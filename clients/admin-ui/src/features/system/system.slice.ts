import { createSelector, createSlice, PayloadAction } from "@reduxjs/toolkit";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import type { RootState } from "~/app/store";
import { selectToken } from "~/features/auth";
import { addCommonHeaders } from "~/features/common/CommonHeaders";
import { System } from "~/types/api";

interface SystemDeleteResponse {
  message: string;
  resource: System;
}

interface UpsertResponse {
  message: string;
  inserted: number;
  updated: number;
}

export const systemApi = createApi({
  reducerPath: "systemApi",
  baseQuery: fetchBaseQuery({
    baseUrl: process.env.NEXT_PUBLIC_FIDESCTL_API,
    prepareHeaders: (headers, { getState }) => {
      const token: string | null = selectToken(getState() as RootState);
      addCommonHeaders(headers, token);
      return headers;
    },
  }),
  tagTypes: ["System"],
  endpoints: (build) => ({
    getAllSystems: build.query<System[], void>({
      query: () => ({ url: `system/` }),
      providesTags: () => ["System"],
    }),
    getSystemByFidesKey: build.query<System, string>({
      query: (fides_key) => ({ url: `system/${fides_key}/` }),
      providesTags: ["System"],
    }),
    // we accept 'unknown' as well since the user can paste anything in, and we rely
    // on the backend to do the validation for us
    createSystem: build.mutation<System, System | unknown>({
      query: (body) => ({
        url: `system/`,
        method: "POST",
        body,
      }),
      invalidatesTags: () => ["System"],
    }),
    deleteSystem: build.mutation<SystemDeleteResponse, string>({
      query: (key) => ({
        url: `system/${key}`,
        params: { resource_type: "system" },
        method: "DELETE",
      }),
      invalidatesTags: ["System"],
    }),
    upsertSystems: build.mutation<UpsertResponse, System[]>({
      query: (systems) => ({
        url: `/system/upsert`,
        method: "POST",
        body: systems,
      }),
      invalidatesTags: ["System"],
    }),
    updateSystem: build.mutation<
      System,
      Partial<System> & Pick<System, "fides_key">
    >({
      query: ({ ...patch }) => ({
        url: `system/`,
        params: { resource_type: "system" },
        method: "PUT",
        body: patch,
      }),
      invalidatesTags: ["System"],
      // For optimistic updates
      async onQueryStarted(
        { fides_key, ...patch },
        { dispatch, queryFulfilled }
      ) {
        const patchResult = dispatch(
          systemApi.util.updateQueryData(
            "getSystemByFidesKey",
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
           * dispatch(api.util.invalidateTags(['System']))
           */
        }
      },
    }),
  }),
});

export const {
  useGetAllSystemsQuery,
  useGetSystemByFidesKeyQuery,
  useCreateSystemMutation,
  useUpdateSystemMutation,
  useDeleteSystemMutation,
  useUpsertSystemsMutation,
} = systemApi;

export interface State {
  activeSystem?: System;
  activeClassifySystemFidesKey?: string;
  systemsToClassify?: System[];
}
const initialState: State = {};

export const systemSlice = createSlice({
  name: "system",
  initialState,
  reducers: {
    setActiveSystem: (
      draftState,
      action: PayloadAction<System | undefined>
    ) => {
      draftState.activeSystem = action.payload;
    },
    setActiveClassifySystemFidesKey: (
      draftState,
      action: PayloadAction<string | undefined>
    ) => {
      draftState.activeClassifySystemFidesKey = action.payload;
    },
    setSystemsToClassify: (
      draftState,
      action: PayloadAction<System[] | undefined>
    ) => {
      draftState.systemsToClassify = action.payload;
    },
  },
});

export const {
  setActiveSystem,
  setActiveClassifySystemFidesKey,
  setSystemsToClassify,
} = systemSlice.actions;

export const { reducer } = systemSlice;

const selectSystem = (state: RootState) => state.system;

export const selectActiveSystem = createSelector(
  selectSystem,
  (state) => state.activeSystem
);

export const selectActiveClassifySystemFidesKey = createSelector(
  selectSystem,
  (state) => state.activeClassifySystemFidesKey
);

export const selectAllSystems = createSelector(
  systemApi.endpoints.getAllSystems.select(),
  ({ data }) => data
);

export const selectActiveClassifySystem = createSelector(
  [selectAllSystems, selectActiveClassifySystemFidesKey],
  (allSystems, fidesKey) => {
    if (fidesKey === undefined) {
      return undefined;
    }

    const system = allSystems?.find((s) => s.fides_key === fidesKey);
    return system;
  }
);

export const selectSystemsToClassify = createSelector(
  selectSystem,
  (state) => state.systemsToClassify
);
