import { createSelector } from "@reduxjs/toolkit";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import {
  selectActiveCollection,
  selectActiveDatasetFidesKey,
  selectActiveField,
} from "~/features/dataset/dataset.slice";
import { GenerateRequestPayload } from "~/types/api";

interface HealthResponse {
  core_fidesctl_version: string;
  status: "healthy";
}

/**
 * These interfaces will be replaced with the OpenAPI generated models when the backend is ready.
 */
export interface ClassifyInstanceRequest {
  // Array of objects because we might need to match by more DB info than just the fides_key.
  datasets: Array<{
    fides_key: string;
    name?: string;
  }>;
  schema_config: GenerateRequestPayload;
}

// TODO(ssangervasi): Resolves the assumptions commented below when the API is done.
// https://github.com/ethyca/fidesctl-plus/pull/106#pullrequestreview-1112775197
export interface Classification {
  label: string;
  score: number;
  aggregated_score: number;
  classification_paradigm: string;
}
export interface ClassifyField {
  name: string;
  classifications: Classification[];
}
export interface ClassifyCollection {
  name: string;
  fields: ClassifyField[];
}
export interface ClassifyDataset {
  fides_key: string;
  // Assuming these are empty while the instance is in the "processing" status.
  collections: ClassifyCollection[];
  status: ClassifyStatusEnum;
}
export enum ClassifyStatusEnum {
  CREATED = "Created",
  IN_WORK = "In Work",
  COMPLETE = "Complete",
  FAILED = "Failed",
  // Name TBD by the backend.
  REVIEWED = "Reviewed",
}
export interface ClassifyInstanceValues {
  id: string;
  status: ClassifyStatusEnum;
  organization_fides_key: string;
  dataset_fides_key: string;
  dataset_name: string;
}
export interface ClassifyDatasetResponse {
  classify_instances: ClassifyInstanceValues[];
}
export interface ClassificationResponse {
  datasets: ClassifyDataset[];
}
export interface ClassifyInstanceUpdateRequest {
  dataset_fides_key: string;
  status: ClassifyStatusEnum;
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
      ClassifyInstanceRequest
    >({
      query: (body) => ({
        url: `classify/`,
        method: "POST",
        body,
      }),
      invalidatesTags: ["ClassifyInstances"],
    }),
    updateClassifyInstance: build.mutation<void, ClassifyInstanceUpdateRequest>(
      {
        query: (body) => ({
          url: `classify/`,
          method: "PUT",
          body,
        }),
        invalidatesTags: ["ClassifyInstances"],
      }
    ),
    getAllClassifyInstances: build.query<ClassifyInstanceValues[], void>({
      query: () => `classify/`,
      providesTags: ["ClassifyInstances"],
    }),
  }),
});

export const {
  useGetHealthQuery,
  useCreateClassifyInstanceMutation,
  useGetAllClassifyInstancesQuery,
  useUpdateClassifyInstanceMutation,
} = plusApi;

export const useHasPlus = () => {
  const { isSuccess: hasPlus } = useGetHealthQuery();
  return hasPlus;
};

const emptyClassifyInstances: ClassifyInstanceValues[] = [];
export const selectClassifyInstances = createSelector(
  plusApi.endpoints.getAllClassifyInstances.select(),
  ({ data: instances }) => instances ?? emptyClassifyInstances
);

const emptyClassifyInstanceMap: Map<string, ClassifyInstanceValues> = new Map();
export const selectClassifyInstanceMap = createSelector(
  selectClassifyInstances,
  (instances) => {
    const map = new Map<string, ClassifyInstanceValues>();
    instances.forEach((ci) => {
      map.set(ci.dataset_fides_key, ci);
    });

    if (map.size === 0) {
      return emptyClassifyInstanceMap;
    }

    return map;
  }
);

/**
 * ClassifyInstance selectors that parallel the dataset's structure. These used the
 * cached getAllClassifyInstances response state, as well as the "active" dataset according
 * to the dataset feature's state.
 */
export const selectClassifyInstanceDataset = createSelector(
  [selectClassifyDatasetMap, selectActiveDatasetFidesKey],
  (classifyDatasetMap, fidesKey) =>
    classifyDatasetMap && fidesKey
      ? classifyDatasetMap.get(fidesKey)
      : undefined
);

const emptyCollectionMap: Map<string, ClassifyCollection> = new Map();
export const selectClassifyInstanceCollectionMap = createSelector(
  selectClassifyInstanceDataset,
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
