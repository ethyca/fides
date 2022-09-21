import { createSelector } from "@reduxjs/toolkit";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import {
  selectActiveCollection,
  selectActiveDatasetFidesKey,
  selectActiveField,
} from "~/features/dataset/dataset.slice";
import { DatasetCollection, DatasetField, Generate } from "~/types/api";

interface HealthResponse {
  core_fidesctl_version: string;
  status: "healthy";
}

/**
 * These interfaces will be replaced with the OpenAPI generated models when the backend is ready.
 */
interface ClassifyInstanceRequest {
  organization_key: string;
  // Array of objects because we might need to match by more DB info than just the fides_key.
  datasets: Array<{
    fides_key: "string";
  }>;
  generate: Generate;
}

// TODO(ssangervasi): Resolves the assumptions commented below when the API is done.
// https://github.com/ethyca/fidesctl-plus/pull/106#pullrequestreview-1112775197
interface Classification {
  label: string;
  score: number;
  aggregated_score: number;
  classification_paradigm: string;
}
interface ClassifyField {
  name: string;
  classifications: Classification[];
}
interface ClassifyCollection {
  name: string;
  fields: ClassifyField[];
}
interface ClassifyDataset {
  fides_key: string;
  collections: ClassifyCollection[];
}
interface ClassifyInstance {
  // ClassifyInstances probably have a UID not a key
  id: string;
  // Probably will become an enum.
  status: "processing" | "review" | "classified";
  // Assuming these are blank while in the "processing" status.
  datasets?: ClassifyDataset;
}

export const plusApi = createApi({
  reducerPath: "plusApi",
  baseQuery: fetchBaseQuery({
    baseUrl: `${process.env.NEXT_PUBLIC_FIDESCTL_API}/plus`,
  }),
  tagTypes: ["Plus"],
  endpoints: (build) => ({
    getHealth: build.query<HealthResponse, void>({
      query: () => "health",
    }),
    /**
     * Fidescls endpoints:
     */
    createClassifyInstance: build.mutation<
      ClassifyInstanceResponse,
      ClassifyInstanceRequest
    >({
      query: (body) => ({
        url: `classify/`,
        method: "POST",
        body,
      }),
    }),
    getAllClassifyInstances: build.query<ClassifyInstance[], void>({
      query: () => `classify/`,
    }),
  }),
});

export const {
  useGetHealthQuery,
  useCreateClassifyInstanceMutation,
  useGetAllClassifyInstancesQuery,
} = plusApi;

export const useHasPlus = () => {
  const { isSuccess: hasPlus } = useGetHealthQuery();
  return hasPlus;
};

const emptyClassifyInstances: ClassifyInstanceResponse[] = [];
const selectClassifyInstancesMap = createSelector(
  ({ data }: { data?: ClassifyInstanceResponse[] }) =>
    data ?? emptyClassifyInstances,
  (classifyInstances) => ({
    map: new Map(classifyInstances.map((c) => [c.fides_key, c])),
  })
);

/**
 * Convenience hook for looking up a ClassifyInstance by Dataset key.
 */
export const useClassifyInstancesMap = (): Map<
  string,
  ClassifyInstanceResponse
> => {
  const hasPlus = useHasPlus();
  const { map } = useGetAllClassifyInstancesQuery(undefined, {
    skip: !hasPlus,
    selectFromResult: selectClassifyInstancesMap,
  });
  return map;
};

/**
 * ClassifyInstance selectors that parallel the dataset's structure. These used the
 * cached getAllClassifyInstances response state, as well as the "active" dataset according
 * to the dataset feature's state.
 */
export const selectActiveClassifyInstance = createSelector(
  [
    plusApi.endpoints.getAllClassifyInstances.select(),
    selectActiveDatasetFidesKey,
  ],
  ({ data: responses }, fidesKey) =>
    responses?.find((c) => c.fides_key === fidesKey)?.classifyInstance
);

const emptyCollectionMap: Map<string, DatasetCollection> = new Map();
export const selectClassifyInstanceCollectionMap = createSelector(
  selectActiveClassifyInstance,
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

const emptyFieldMap: Map<string, DatasetField> = new Map();
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
