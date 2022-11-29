import { createSelector } from "@reduxjs/toolkit";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import {
  selectActiveCollection,
  selectActiveDatasetFidesKey,
  selectActiveField,
} from "~/features/dataset/dataset.slice";
import { selectSystemsToClassify } from "~/features/system";
import {
  ClassificationResponse,
  ClassifyCollection,
  ClassifyDatasetResponse,
  ClassifyEmpty,
  ClassifyField,
  ClassifyInstanceResponseValues,
  ClassifyRequestPayload,
  ClassifyStatusUpdatePayload,
  ClassifySystem,
  GenerateTypes,
  SystemScanResponse,
  SystemsDiff,
} from "~/types/api";

interface HealthResponse {
  core_fidesctl_version: string;
  status: "healthy";
}

interface ScanParams {
  classify?: boolean;
}

interface ClassifyInstancesParams {
  fides_keys?: string[];
  resource_type: GenerateTypes;
}

export const plusApi = createApi({
  reducerPath: "plusApi",
  baseQuery: fetchBaseQuery({
    baseUrl: `${process.env.NEXT_PUBLIC_FIDESCTL_API}/plus`,
  }),
  tagTypes: [
    "Plus",
    "ClassifyInstancesDatasets",
    "ClassifyInstancesSystems",
    "LatestScan",
  ],
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
      invalidatesTags: ["ClassifyInstancesDatasets"],
    }),
    updateClassifyInstance: build.mutation<
      void,
      ClassifyStatusUpdatePayload & { resource_type?: GenerateTypes }
    >({
      query: (payload) => {
        // eslint-disable-next-line @typescript-eslint/naming-convention
        const { resource_type = GenerateTypes.DATASETS, ...body } = payload;
        return {
          url: `classify/`,
          method: "PUT",
          params: { resource_type },
          body,
        };
      },
      invalidatesTags: (response, errors, args) => {
        if (args.resource_type === GenerateTypes.SYSTEMS) {
          return ["ClassifyInstancesSystems"];
        }
        return ["ClassifyInstancesDatasets"];
      },
    }),
    getAllClassifyInstances: build.query<
      ClassifyInstanceResponseValues[],
      ClassifyInstancesParams
    >({
      query: (params) => {
        const urlParams = new URLSearchParams();
        urlParams.append("resource_type", params.resource_type);
        params.fides_keys?.forEach((key) => {
          urlParams.append("fides_keys", key);
        });
        return {
          url: `classify/?${urlParams.toString()}`,
          method: "GET",
        };
      },
      providesTags: (response, errors, args) => {
        if (args.resource_type === GenerateTypes.SYSTEMS) {
          return ["ClassifyInstancesSystems"];
        }
        return ["ClassifyInstancesDatasets"];
      },
    }),
    getClassifyDataset: build.query<ClassificationResponse, string>({
      query: (dataset_fides_key: string) => ({
        url: `classify/details/${dataset_fides_key}`,
        params: { resource_type: GenerateTypes.DATASETS },
      }),
      providesTags: ["ClassifyInstancesDatasets"],
    }),
    getClassifySystem: build.query<ClassifySystem | ClassifyEmpty, string>({
      query: (fidesKey: string) => ({
        url: `classify/details/${fidesKey}`,
        params: { resource_type: GenerateTypes.SYSTEMS },
      }),
      providesTags: ["ClassifyInstancesSystems"],
    }),

    // Kubernetes Cluster Scanner
    updateScan: build.mutation<SystemScanResponse, ScanParams>({
      query: (params: ScanParams) => ({
        url: `scan`,
        params,
        method: "PUT",
      }),
      invalidatesTags: ["ClassifyInstancesSystems", "LatestScan"],
    }),
    getLatestScanDiff: build.query<SystemsDiff, void>({
      query: () => ({
        url: `scan/latest`,
        params: { diff: true },
        method: "GET",
      }),
      providesTags: ["LatestScan"],
    }),
  }),
});

export const {
  useGetHealthQuery,
  useCreateClassifyInstanceMutation,
  useGetAllClassifyInstancesQuery,
  useGetClassifyDatasetQuery,
  useGetClassifySystemQuery,
  useUpdateClassifyInstanceMutation,
  useUpdateScanMutation,
  useGetLatestScanDiffQuery,
  useLazyGetLatestScanDiffQuery,
} = plusApi;

export const useHasPlus = () => {
  const { isSuccess: hasPlus } = useGetHealthQuery();
  return hasPlus;
};

const emptyClassifyInstances: ClassifyInstanceResponseValues[] = [];
export const selectDatasetClassifyInstances = createSelector(
  plusApi.endpoints.getAllClassifyInstances.select({
    resource_type: GenerateTypes.DATASETS,
  }),
  ({ data: instances }) => instances ?? emptyClassifyInstances
);

export const selectSystemClassifyInstances = createSelector(
  [(state) => state, selectSystemsToClassify],
  (state, systems) =>
    plusApi.endpoints.getAllClassifyInstances.select({
      resource_type: GenerateTypes.SYSTEMS,
      fides_keys: systems?.map((s) => s.fides_key),
    })(state)?.data ?? emptyClassifyInstances
);

const emptyClassifyInstanceMap: Map<string, ClassifyInstanceResponseValues> =
  new Map();

const instancesToMap = (instances: ClassifyInstanceResponseValues[]) => {
  const map = new Map<string, ClassifyInstanceResponseValues>();
  instances.forEach((ci) => {
    map.set(ci.dataset_key, ci);
  });

  if (map.size === 0) {
    return emptyClassifyInstanceMap;
  }

  return map;
};

export const selectDatasetClassifyInstanceMap = createSelector(
  selectDatasetClassifyInstances,
  (instances) => instancesToMap(instances)
);

export const selectSystemClassifyInstanceMap = createSelector(
  selectSystemClassifyInstances,
  (instances) => instancesToMap(instances)
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
