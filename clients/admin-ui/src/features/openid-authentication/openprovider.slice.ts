import { createSelector, createSlice, PayloadAction } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";
import { baseApi } from "~/features/common/api.slice";
import {
  OpenIDProvider,
  SystemResponse,
} from "~/types/api";

interface SystemDeleteResponse {
  message: string;
  resource: OpenIDProvider;
}

const openIDProviderApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAllOpenIDProviders: build.query<SystemResponse[], void>({
      query: () => ({ url: `plus/openid-provider` }),
    //   providesTags: () => ["System"],
    //   transformResponse: (systems: SystemResponse[]) =>
    //     systems.sort((a, b) => {
    //       const displayName = (system: SystemResponse) =>
    //         system.name === "" || system.name == null
    //           ? system.fides_key
    //           : system.name;
    //       return displayName(a).localeCompare(displayName(b));
    //     }),
    }),
    // getSystemByFidesKey: build.query<SystemResponse, string>({
    //   query: (fides_key) => ({ url: `openid-provider/${fides_key}` }),
    //   providesTags: ["System"],
    // }),
    // we accept 'unknown' as well since the user can paste anything in, and we rely
    // on the backend to do the validation for us
    createOpenIDProvider: build.mutation<SystemResponse, OpenIDProvider | unknown>({
      query: (body) => ({
        url: `plus/openid-provider`,
        method: "POST",
        body,
      }),
    //   invalidatesTags: () => [
    //     "Datamap",
    //     "System",
    //     "Datastore Connection",
    //     "System Vendors",
    //     "Privacy Notices",
    //   ],
    }),
    // deleteSystem: build.mutation<SystemDeleteResponse, string>({
    //   query: (key) => ({
    //     url: `openid-provider/${key}`,
    //     params: { resource_type: "system" },
    //     method: "DELETE",
    //   }),
    //   invalidatesTags: [
    //     "Datamap",
    //     "System",
    //     "Datastore Connection",
    //     "Privacy Notices",
    //     "System Vendors",
    //   ],
    // }),
    updateOpenIDProvider: build.mutation<
      SystemResponse,
      Partial<OpenIDProvider> & Pick<OpenIDProvider, "fides_key">
    >({
      query: ({ ...patch }) => ({
        url: `plus/openid-provider`,
        // params: { resource_type: "system" },
        method: "PUT",
        body: patch,
      }),
      // invalidatesTags: [
      //   "Datamap",
      //   "System",
      //   "Privacy Notices",
      //   "Datastore Connection",
      //   "System History",
      //   "System Vendors",
      // ],
    }),
  }),
});

export const {
  useGetAllOpenIDProvidersQuery,
//   useGetSystemByFidesKeyQuery,
  useCreateOpenIDProviderMutation,
  useUpdateOpenIDProviderMutation,
//   useDeleteSystemMutation,
} = openIDProviderApi;

// export interface State {
//   activeSystem?: System;
//   activeClassifySystemFidesKey?: string;
//   systemsToClassify?: System[];
// }
// const initialState: State = {};

// export const systemSlice = createSlice({
//   name: "system",
//   initialState,
//   reducers: {
//     setActiveSystem: (
//       draftState,
//       action: PayloadAction<System | undefined>
//     ) => {
//       draftState.activeSystem = action.payload;
//     },
//     setActiveClassifySystemFidesKey: (
//       draftState,
//       action: PayloadAction<string | undefined>
//     ) => {
//       draftState.activeClassifySystemFidesKey = action.payload;
//     },
//     setSystemsToClassify: (
//       draftState,
//       action: PayloadAction<System[] | undefined>
//     ) => {
//       draftState.systemsToClassify = action.payload;
//     },
//   },
// });

// export const {
//   setActiveSystem,
//   setActiveClassifySystemFidesKey,
//   setSystemsToClassify,
// } = systemSlice.actions;

// export const { reducer } = systemSlice;

// const selectSystem = (state: RootState) => state.system;

// export const selectActiveSystem = createSelector(
//   selectSystem,
//   (state) => state.activeSystem
// );

// export const selectActiveClassifySystemFidesKey = createSelector(
//   selectSystem,
//   (state) => state.activeClassifySystemFidesKey
// );

// const emptySelectAllSystems: SystemResponse[] = [];
// export const selectAllSystems = createSelector(
//   [(RootState) => RootState, openIDProviderApi.endpoints.getAllSystems.select()],
//   (RootState, { data }) => data || emptySelectAllSystems
// );

// export const selectActiveClassifySystem = createSelector(
//   [selectAllSystems, selectActiveClassifySystemFidesKey],
//   (allSystems, fidesKey) => {
//     if (fidesKey === undefined) {
//       return undefined;
//     }
//     const system = allSystems?.find((s) => s.fides_key === fidesKey);
//     return system;
//   }
// );

// export const selectSystemsToClassify = createSelector(
//   selectSystem,
//   (state) => state.systemsToClassify
// );
