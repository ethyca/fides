import { createSelector } from "@reduxjs/toolkit";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import {
  selectActiveCollection,
  selectActiveDatasetFidesKey,
  selectActiveField,
} from "~/features/dataset/dataset.slice";
import { Dataset, DatasetCollection, DatasetField } from "~/types/api";

interface HealthResponse {
  core_fidesctl_version: string;
  status: "healthy";
}

/**
 * These interfaces will be replaced with the OpenAPI generated models when the backend is ready.
 */
interface ClassificationRequest {
  // Key of the dataset. Should this have "dataset_" prefix?
  fides_key: string;
}
// TODO(ssangervasi): Resolves the assumptions commented below when the API is done.
// The API in its current WIP state flattens the list of fields instead of matching the dataset's
// nested structure: https://github.com/ethyca/fidesctl-plus/pull/106#pullrequestreview-1112775197
interface ClassificationResponse {
  // Classifications probably have a UID not a key
  id: string;
  // Dataset key
  fides_key: string;
  // Probably will become an enum.
  status: "processing" | "review" | "classified";
  // Assuming these are blank while in the "processing" status. This extra nesting under
  // "classification" might be wrong. Hoisting these properties would make the classification mirror
  // the dataset structure better.
  classification?: Pick<Dataset, "data_categories" | "collections">;
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
    createClassification: build.mutation<
      ClassificationResponse,
      ClassificationRequest
    >({
      query: (body) => ({
        // Or is this "classify/"?
        url: `classification/`,
        method: "POST",
        body,
      }),
    }),
    getAllClassifications: build.query<ClassificationResponse[], void>({
      query: () => `classification/`,
    }),
  }),
});

export const {
  useGetHealthQuery,
  useCreateClassificationMutation,
  useGetAllClassificationsQuery,
} = plusApi;

export const useHasPlus = () => {
  const { isSuccess: hasPlus } = useGetHealthQuery();
  return hasPlus;
};

const emptyClassifications: ClassificationResponse[] = [];
const selectClassificationsMap = createSelector(
  ({ data }: { data?: ClassificationResponse[] }) =>
    data ?? emptyClassifications,
  (classifications) => ({
    map: new Map(classifications.map((c) => [c.fides_key, c])),
  })
);

/**
 * Convenience hook for looking up a Classification by Dataset key.
 */
export const useClassificationsMap = (): Map<
  string,
  ClassificationResponse
> => {
  const hasPlus = useHasPlus();
  const { map } = useGetAllClassificationsQuery(undefined, {
    skip: !hasPlus,
    selectFromResult: selectClassificationsMap,
  });
  return map;
};

/**
 * Classification selectors that parallel the dataset's structure. These used the
 * cached getAllClassifications response state, as well as the "active" dataset according
 * to the dataset feature's state.
 */
export const selectActiveClassification = createSelector(
  [
    plusApi.endpoints.getAllClassifications.select(),
    selectActiveDatasetFidesKey,
  ],
  ({ data: responses }, fidesKey) =>
    responses?.find((c) => c.fides_key === fidesKey)?.classification
);

const emptyCollectionMap: Map<string, DatasetCollection> = new Map();
export const selectClassificationCollectionMap = createSelector(
  selectActiveClassification,
  (classification) =>
    classification?.collections
      ? new Map(classification.collections.map((c) => [c.name, c]))
      : emptyCollectionMap
);
export const selectClassificationCollection = createSelector(
  [selectClassificationCollectionMap, selectActiveCollection],
  (collectionMap, active) =>
    active ? collectionMap.get(active.name) : undefined
);

const emptyFieldMap: Map<string, DatasetField> = new Map();
export const selectClassificationFieldMap = createSelector(
  selectClassificationCollection,
  (collection) =>
    collection?.fields
      ? new Map(collection.fields.map((f) => [f.name, f]))
      : emptyFieldMap
);
/**
 * Note that this selects the field that is currently active in the editor. Fields that are shown in
 * the table are looked up by their name using selectClassificationFieldMap.
 */
export const selectClassificationField = createSelector(
  [selectClassificationFieldMap, selectActiveField],
  (fieldMap, active) => (active ? fieldMap.get(active.name) : undefined)
);
