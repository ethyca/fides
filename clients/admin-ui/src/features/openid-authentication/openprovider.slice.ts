import { baseApi } from "~/features/common/api.slice";
import {
  OpenIDProvider,
  SystemResponse,
} from "~/types/api";

interface OpenIDProviderDeleteResponse {
  message: string;
  resource: OpenIDProvider;
}

const openIDProviderApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAllOpenIDProviders: build.query<SystemResponse[], void>({
      query: () => ({ url: `plus/openid-provider` }),
    }),
    createOpenIDProvider: build.mutation<SystemResponse, OpenIDProvider | unknown>({
      query: (body) => ({
        url: `plus/openid-provider`,
        method: "POST",
        body,
      }),
    }),
    deleteOpenIDProvider: build.mutation<OpenIDProviderDeleteResponse, string>({
      query: (key) => ({
        url: `openid-provider/${key}`,
        method: "DELETE",
      }),
    }),
    updateOpenIDProvider: build.mutation<
      SystemResponse,
      Partial<OpenIDProvider> & Pick<OpenIDProvider, "fides_key">
    >({
      query: ({ ...patch }) => ({
        url: `plus/openid-provider`,
        method: "PUT",
        body: patch,
      }),
    }),
  }),
});

export const {
  useGetAllOpenIDProvidersQuery,
  useCreateOpenIDProviderMutation,
  useUpdateOpenIDProviderMutation,
  useDeleteOpenIDProviderMutation,
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
