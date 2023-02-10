import { createSelector } from "@reduxjs/toolkit";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";
import { addCommonHeaders } from "common/CommonHeaders";

import type { RootState } from "~/app/store";
import { selectToken } from "~/features/auth";
import {
  selectActiveCollection,
  selectActiveDatasetFidesKey,
  selectActiveField,
} from "~/features/dataset/dataset.slice";
import { selectSystemsToClassify } from "~/features/system";
import {
  AllowList,
  AllowListUpdate,
  ClassificationResponse,
  ClassifyCollection,
  ClassifyDatasetResponse,
  ClassifyEmpty,
  ClassifyField,
  ClassifyInstanceResponseValues,
  ClassifyRequestPayload,
  ClassifyStatusUpdatePayload,
  ClassifySystem,
  CustomFieldDefinition,
  CustomFieldDefinitionWithId,
  CustomFieldWithId,
  GenerateTypes,
  HealthCheck,
  ResourceTypes,
  System,
  SystemScannerStatus,
  SystemScanResponse,
  SystemsDiff,
} from "~/types/api";

interface ScanParams {
  classify?: boolean;
}

interface ClassifyInstancesParams {
  fides_keys?: string[];
  resource_type: GenerateTypes;
}

export type WebsiteScan = {
  url: string;
  name: string;
};

const plusBaseUrl = `${process.env.NEXT_PUBLIC_FIDESCTL_API}/plus`;
export const plusApi = createApi({
  reducerPath: "plusApi",
  baseQuery: fetchBaseQuery({
    baseUrl: plusBaseUrl,
    prepareHeaders: (headers, { getState }) => {
      const token: string | null = selectToken(getState() as RootState);
      addCommonHeaders(headers, token);
      return headers;
    },
  }),
  tagTypes: [
    "AllowList",
    "ClassifyInstancesDatasets",
    "ClassifyInstancesSystems",
    "CustomFieldDefinition",
    "CustomFields",
    "LatestScan",
    "Plus",
    "Webscan",
  ],
  endpoints: (build) => ({
    getHealth: build.query<HealthCheck, void>({
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

    // Custom Metadata Allow List
    getAllAllowList: build.query<AllowList[], boolean>({
      query: (show_values: boolean) => ({
        url: `custom-metadata/allow-list`,
        params: { show_values },
      }),
      providesTags: ["AllowList"],
    }),
    upsertAllowList: build.mutation<AllowList, AllowListUpdate>({
      query: (params: AllowListUpdate) => ({
        url: `custom-metadata/allow-list`,
        method: "PUT",
        body: params,
      }),
      invalidatesTags: ["AllowList"],
    }),

    // Custom Metadata Custom Field
    getCustomFieldsForResource: build.query<CustomFieldWithId[], string>({
      query: (resource_id: string) => ({
        url: `custom-metadata/custom-field/resource/${resource_id}`,
      }),
      providesTags: ["CustomFields"],
    }),
    upsertCustomField: build.mutation<CustomFieldWithId, CustomFieldWithId>({
      query: (params) => ({
        url: `custom-metadata/custom-field`,
        method: "PUT",
        body: {
          custom_field_definition_id: params.custom_field_definition_id,
          id: params.id,
          resource_id: params.resource_id,
          value: params.value,
        },
      }),
      invalidatesTags: ["CustomFields"],
    }),

    // Custom Metadata Custom Field Definition
    addCustomFieldDefinition: build.mutation<
      CustomFieldDefinitionWithId,
      CustomFieldDefinition
    >({
      query: (params) => ({
        url: `custom-metadata/custom-field-definition`,
        method: "POST",
        body: params,
      }),
      invalidatesTags: ["CustomFieldDefinition"],
    }),

    // Custom Metadata Custom Field Definition By Resource Type
    getCustomFieldDefinitionsByResourceType: build.query<
      CustomFieldDefinitionWithId[],
      ResourceTypes
    >({
      query: (resource_type: ResourceTypes) => ({
        url: `custom-metadata/custom-field-definition/resource-type/${resource_type}`,
      }),
      providesTags: ["CustomFieldDefinition"],
    }),

    getWebScan: build.mutation<System[], WebsiteScan>({
      query: ({ url, name }) => ({
        url: `${plusBaseUrl}/web-scan/latest?url=${url}&name=${name}&diff=True`,
        method: "GET",
      }),
      invalidatesTags: ["Webscan"],
    }),
  }),
});

export const {
  useUpsertCustomFieldMutation,
  useUpsertAllowListMutation,
  useUpdateScanMutation,
  useUpdateClassifyInstanceMutation,
  useLazyGetLatestScanDiffQuery,
  useGetLatestScanDiffQuery,
  useGetHealthQuery,
  useGetCustomFieldsForResourceQuery,
  useGetCustomFieldDefinitionsByResourceTypeQuery,
  useGetClassifySystemQuery,
  useGetClassifyDatasetQuery,
  useGetAllClassifyInstancesQuery,
  useGetAllAllowListQuery,
  useCreateClassifyInstanceMutation,
  useAddCustomFieldDefinitionMutation,
  useGetWebScanMutation,
} = plusApi;

export const selectHealth: (state: RootState) => HealthCheck | undefined =
  createSelector(plusApi.endpoints.getHealth.select(), ({ data }) => data);

export const selectDataFlowScannerStatus: (
  state: RootState
) => SystemScannerStatus | undefined = createSelector(
  plusApi.endpoints.getHealth.select(),
  ({ data }) => data?.system_scanner
);

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
