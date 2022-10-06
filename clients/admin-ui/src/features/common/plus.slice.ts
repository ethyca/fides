import { createSelector } from "@reduxjs/toolkit";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import {
  selectActiveCollection,
  selectActiveDatasetFidesKey,
  selectActiveField,
} from "~/features/dataset/dataset.slice";
import {
  ClassificationResponse,
  ClassifyCollection,
  ClassifyDatasetResponse,
  ClassifyField,
  ClassifyInstanceResponseValues,
  ClassifyRequestPayload,
  ClassifyStatusUpdatePayload,
} from "~/types/api";

interface HealthResponse {
  core_fidesctl_version: string;
  status: "healthy";
}

export const plusApi = createApi({
  reducerPath: "plusApi",
  baseQuery: fetchBaseQuery({
    baseUrl: `${process.env.NEXT_PUBLIC_FIDESCTL_API}/plus`,
  }),
  tagTypes: ["Plus", "ClassifyInstances"],
  endpoints: (build) => ({
    getHealth: build.query<HealthResponse, void>({
      query: () => "health",
    }),
    /**
     * Fidescls endpoints:
     */
    createClassifyInstance: build.mutation<
      ClassifyDatasetResponse,
      ClassifyRequestPayload
    >({
      query: (body) => ({
        url: `classify/`,
        method: "POST",
        body,
      }),
      invalidatesTags: ["ClassifyInstances"],
    }),
    updateClassifyInstance: build.mutation<void, ClassifyStatusUpdatePayload>({
      query: (body) => ({
        url: `classify/`,
        method: "PUT",
        body,
      }),
      invalidatesTags: ["ClassifyInstances"],
    }),
    getAllClassifyInstances: build.query<
      ClassifyInstanceResponseValues[],
      void
    >({
      query: () => `classify/`,
      providesTags: ["ClassifyInstances"],
    }),
    getClassifyDataset: build.query<ClassificationResponse, string>({
      query: (dataset_fides_key: string) =>
        `classify/details/${dataset_fides_key}`,
      providesTags: ["ClassifyInstances"],
    }),
  }),
});

export const {
  useGetHealthQuery,
  useCreateClassifyInstanceMutation,
  useGetAllClassifyInstancesQuery,
  useGetClassifyDatasetQuery,
  useUpdateClassifyInstanceMutation,
} = plusApi;

export const useHasPlus = () => {
  const { isSuccess: hasPlus } = useGetHealthQuery();
  return hasPlus;
};

const emptyClassifyInstances: ClassifyInstanceResponseValues[] = [];
export const selectClassifyInstances = createSelector(
  plusApi.endpoints.getAllClassifyInstances.select(),
  ({ data: instances }) => instances ?? emptyClassifyInstances
);

const emptyClassifyInstanceMap: Map<string, ClassifyInstanceResponseValues> =
  new Map();
export const selectClassifyInstanceMap = createSelector(
  selectClassifyInstances,
  (instances) => {
    const map = new Map<string, ClassifyInstanceResponseValues>();
    instances.forEach((ci) => {
      map.set(ci.dataset_key, ci);
    });

    if (map.size === 0) {
      return emptyClassifyInstanceMap;
    }

    return map;
  }
);

/**
 * This is the root of ClassifyInstance selectors that parallel the dataset's structure. These used
 * the cached getClassifyDataset response state, which is a query using  the "active" dataset's
 * fides_key.
 */
export const selectActiveClassifyDataset = createSelector(
  // The endpoint `select` utility returns a function that runs on the root state.
  [(state) => state, selectActiveDatasetFidesKey],
  (state, fidesKey) =>
    fidesKey
      ? plusApi.endpoints.getClassifyDataset.select(fidesKey)(state)?.data
          ?.datasets?.[0]
      : undefined
);

const emptyCollectionMap: Map<string, ClassifyCollection> = new Map();
export const selectClassifyInstanceCollectionMap = createSelector(
  selectActiveClassifyDataset,
  (classifyInstance) =>
    classifyInstance?.collections
      ? new Map(classifyInstance.collections.map((c) => [c.name, c]))
      : emptyCollectionMap
);
export const selectClassifyInstanceCollection = createSelector(
  [selectClassifyInstanceCollectionMap, selectActiveCollection],
  (collectionMap, active) =>
    active ? collectionMap.get(active.name) : undefined
);

const emptyFieldMap: Map<string, ClassifyField> = new Map();
export const selectClassifyInstanceFieldMap = createSelector(
  selectClassifyInstanceCollection,
  (collection) =>
    collection?.fields
      ? new Map(collection.fields.map((f) => [f.name, f]))
      : emptyFieldMap
);
/**
 * Note that this selects the field that is currently active in the editor. Fields that are shown in
 * the table are looked up by their name using selectClassifyInstanceFieldMap.
 */
export const selectClassifyInstanceField = createSelector(
  [selectClassifyInstanceFieldMap, selectActiveField],
  (fieldMap, active) => (active ? fieldMap.get(active.name) : undefined)
);
