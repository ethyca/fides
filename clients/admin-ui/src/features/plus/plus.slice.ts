import { createSelector } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";
import { baseApi } from "~/features/common/api.slice";
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

const plusApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getHealth: build.query<HealthCheck, void>({
      query: () => "plus/health",
    }),
    /**
     * Fidescls endpoints:
     */
    createClassifyInstance: build.mutation<
      ClassifyDatasetResponse,
      ClassifyRequestPayload
    >({
      query: (body) => ({
        url: `plus/classify/`,
        method: "POST",
        body,
      }),
      invalidatesTags: ["Classify Instances Datasets"],
    }),
    updateClassifyInstance: build.mutation<
      void,
      ClassifyStatusUpdatePayload & { resource_type?: GenerateTypes }
    >({
      query: (payload) => {
        // eslint-disable-next-line @typescript-eslint/naming-convention
        const { resource_type = GenerateTypes.DATASETS, ...body } = payload;
        return {
          url: `plus/classify/`,
          method: "PUT",
          params: { resource_type },
          body,
        };
      },
      invalidatesTags: (response, errors, args) => {
        if (args.resource_type === GenerateTypes.SYSTEMS) {
          return ["Classify Instances Systems"];
        }
        return ["Classify Instances Datasets"];
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
          url: `plus/classify/?${urlParams.toString()}`,
          method: "GET",
        };
      },
      providesTags: (response, errors, args) => {
        if (args.resource_type === GenerateTypes.SYSTEMS) {
          return ["Classify Instances Systems"];
        }
        return ["Classify Instances Datasets"];
      },
    }),
    getClassifyDataset: build.query<ClassificationResponse, string>({
      query: (dataset_fides_key: string) => ({
        url: `plus/classify/details/${dataset_fides_key}`,
        params: { resource_type: GenerateTypes.DATASETS },
      }),
      providesTags: ["Classify Instances Datasets"],
    }),
    getClassifySystem: build.query<ClassifySystem | ClassifyEmpty, string>({
      query: (fidesKey: string) => ({
        url: `plus/classify/details/${fidesKey}`,
        params: { resource_type: GenerateTypes.SYSTEMS },
      }),
      providesTags: ["Classify Instances Systems"],
    }),

    // Kubernetes Cluster Scanner
    updateScan: build.mutation<SystemScanResponse, ScanParams>({
      query: (params: ScanParams) => ({
        url: `plus/scan`,
        params,
        method: "PUT",
      }),
      invalidatesTags: ["Classify Instances Systems", "Latest Scan"],
    }),
    getLatestScanDiff: build.query<SystemsDiff, void>({
      query: () => ({
        url: `plus/scan/latest`,
        params: { diff: true },
        method: "GET",
      }),
      providesTags: ["Latest Scan"],
    }),

    // Custom Metadata Allow List
    getAllAllowList: build.query<AllowList[], boolean>({
      query: (show_values: boolean) => ({
        url: `plus/custom-metadata/allow-list`,
        params: { show_values },
      }),
      providesTags: ["Allow List"],
      transformResponse: (allowList: AllowList[]) =>
        allowList.sort((a, b) => (a.name ?? "").localeCompare(b.name ?? "")),
    }),
    getAllowList: build.query<AllowList, string>({
      query: (id) => ({
        url: `plus/custom-metadata/allow-list/${id}`,
        params: { show_values: true },
      }),
      providesTags: ["Allow List"],
    }),
    upsertAllowList: build.mutation<AllowList, AllowListUpdate>({
      query: (params: AllowListUpdate) => ({
        url: `plus/custom-metadata/allow-list`,
        method: "PUT",
        body: params,
      }),
      invalidatesTags: ["Allow List"],
    }),

    // Custom Metadata Custom Field
    deleteCustomField: build.mutation<void, { id: string }>({
      query: ({ id }) => ({
        url: `plus/custom-metadata/custom-field/${id}`,
        method: "DELETE",
      }),
      invalidatesTags: ["Custom Fields"],
    }),
    getCustomFieldsForResource: build.query<CustomFieldWithId[], string>({
      query: (resource_id: string) => ({
        url: `plus/custom-metadata/custom-field/resource/${resource_id}`,
      }),
      providesTags: ["Custom Fields"],
    }),
    upsertCustomField: build.mutation<CustomFieldWithId, CustomFieldWithId>({
      query: (params) => ({
        url: `plus/custom-metadata/custom-field`,
        method: "PUT",
        body: {
          custom_field_definition_id: params.custom_field_definition_id,
          id: params.id,
          resource_id: params.resource_id,
          value: params.value,
        },
      }),
      invalidatesTags: ["Custom Fields"],
    }),

    getAllCustomFieldDefinitions: build.query<
      CustomFieldDefinitionWithId[],
      void
    >({
      query: () => ({
        url: `plus/custom-metadata/custom-field-definition`,
      }),
      providesTags: ["Custom Field Definition"],
    }),
    // Custom Metadata Custom Field Definition
    addCustomFieldDefinition: build.mutation<
      CustomFieldDefinitionWithId,
      CustomFieldDefinition
    >({
      query: (params) => ({
        url: `plus/custom-metadata/custom-field-definition`,
        method: "POST",
        body: params,
      }),
      invalidatesTags: ["Custom Field Definition"],
    }),
    updateCustomFieldDefinition: build.mutation<
      CustomFieldDefinitionWithId,
      CustomFieldDefinition
    >({
      query: (params) => ({
        url: `plus/custom-metadata/custom-field-definition`,
        method: "PUT",
        body: params,
      }),
      invalidatesTags: ["Custom Field Definition"],
    }),
    deleteCustomFieldDefinition: build.mutation<void, { id: string }>({
      query: ({ id }) => ({
        url: `plus/custom-metadata/custom-field-definition/${id}`,
        method: "DELETE",
      }),
      invalidatesTags: ["Custom Field Definition"],
    }),

    // Custom Metadata Custom Field Definition By Resource Type
    getCustomFieldDefinitionsByResourceType: build.query<
      CustomFieldDefinitionWithId[],
      ResourceTypes
    >({
      query: (resource_type: ResourceTypes) => ({
        url: `plus/custom-metadata/custom-field-definition/resource-type/${resource_type}`,
      }),
      providesTags: ["Custom Field Definition"],
      transformResponse: (list: CustomFieldDefinitionWithId[]) =>
        list.sort((a, b) => (a.name ?? "").localeCompare(b.name ?? "")),
    }),
  }),
});

export const {
  useAddCustomFieldDefinitionMutation,
  useCreateClassifyInstanceMutation,
  useDeleteCustomFieldMutation,
  useDeleteCustomFieldDefinitionMutation,
  useGetAllAllowListQuery,
  useGetAllClassifyInstancesQuery,
  useGetClassifyDatasetQuery,
  useGetClassifySystemQuery,
  useGetCustomFieldDefinitionsByResourceTypeQuery,
  useGetCustomFieldsForResourceQuery,
  useGetHealthQuery,
  useGetLatestScanDiffQuery,
  useLazyGetLatestScanDiffQuery,
  useUpdateClassifyInstanceMutation,
  useUpdateCustomFieldDefinitionMutation,
  useUpdateScanMutation,
  useUpsertAllowListMutation,
  useUpsertCustomFieldMutation,
  useGetAllCustomFieldDefinitionsQuery,
  useGetAllowListQuery,
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

const emptySelectAllCustomFields: CustomFieldDefinitionWithId[] = [];
export const selectAllCustomFieldDefinitions = createSelector(
  plusApi.endpoints.getAllCustomFieldDefinitions.select(),
  ({ data }) => data || emptySelectAllCustomFields
);
