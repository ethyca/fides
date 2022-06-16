import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";
import { HYDRATE } from "next-redux-wrapper";
import { System } from "./types";

export interface State {
  systems: System[];
}

const initialState: State = {
  systems: [],
};

export const systemApi = createApi({
  reducerPath: "systemApi",
  baseQuery: fetchBaseQuery({
    baseUrl: process.env.NEXT_PUBLIC_FIDESCTL_API,
  }),
  tagTypes: ["System"],
  endpoints: (build) => ({
    getAllSystems: build.query<System[], void>({
      query: () => ({ url: `system/` }),
      providesTags: () => ["System"],
    }),
    getSystemByFidesKey: build.query<Partial<System>, string>({
      query: (fides_key) => ({ url: `system/${fides_key}/` }),
      providesTags: ["System"],
    }),
    createSystem: build.mutation<{}, Partial<System>>({
      query: (body) => ({
        url: `system/`,
        method: "POST",
        body,
      }),
      invalidatesTags: () => ["System"],
    }),
    updateSystem: build.mutation<
      System,
      Partial<System> & Pick<System, "fides_key">
    >({
      query: ({ ...patch }) => ({
        url: `system/`,
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
} = systemApi;

export const systemSlice = createSlice({
  name: "system",
  initialState,
  reducers: {
    setSystems: (state, action: PayloadAction<System[]>) => ({
      systems: action.payload,
    }),
  },
  extraReducers: {
    [HYDRATE]: (state, action) => ({
      ...state,
      ...action.payload.datasets,
    }),
  },
});

export const { setSystems } = systemSlice.actions;

export const { reducer } = systemSlice;
