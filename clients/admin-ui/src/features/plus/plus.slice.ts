import { createSelector } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";
import { CONNECTION_ROUTE } from "~/constants";
import { baseApi } from "~/features/common/api.slice";
import {
  selectActiveCollection,
  selectActiveDatasetFidesKey,
  selectActiveField,
} from "~/features/dataset/dataset.slice";
import { CreateSaasConnectionConfig } from "~/features/datastore-connections";
import { CreateSaasConnectionConfigResponse } from "~/features/datastore-connections/types";
import {
  AllowList,
  AllowListUpdate,
  BulkCustomFieldRequest,
  BulkPutConnectionConfiguration,
  ClassificationResponse,
  ClassifyCollection,
  ClassifyDatasetResponse,
  ClassifyEmpty,
  ClassifyField,
  ClassifyInstanceResponseValues,
  ClassifyRequestPayload,
  ClassifyStatusUpdatePayload,
  ClassifySystem,
  CloudConfig,
  ConnectionConfigurationResponse,
  ConsentableItem,
  CustomAssetType,
  CustomFieldDefinition,
  CustomFieldDefinitionWithId,
  CustomFieldWithId,
  GenerateTypes,
  HealthCheck,
  Page_SystemHistoryResponse_,
  Page_SystemSummary_,
  ResourceTypes,
  SystemPurposeSummary,
  SystemScannerStatus,
  SystemScanResponse,
  SystemsDiff,
  TCFPurposeOverrideSchema,
} from "~/types/api";
import {
  DataUseDeclaration,
  Page_DataUseDeclaration_,
  Page_Vendor_,
} from "~/types/dictionary-api";

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
        url: `plus/classify`,
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
          url: `plus/classify`,
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
          url: `plus/classify?${urlParams.toString()}`,
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
      invalidatesTags: ["Custom Fields", "Datamap"],
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
      invalidatesTags: ["Custom Fields", "Datamap"],
    }),
    bulkUpdateCustomFields: build.mutation<void, BulkCustomFieldRequest>({
      query: (params) => ({
        url: `plus/custom-metadata/custom-field/bulk`,
        method: "POST",
        body: params,
      }),
      invalidatesTags: ["Custom Fields", "Datamap"],
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
      invalidatesTags: ["Custom Field Definition", "Datamap"],
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
      invalidatesTags: ["Custom Field Definition", "Datamap"],
    }),
    deleteCustomFieldDefinition: build.mutation<void, { id: string }>({
      query: ({ id }) => ({
        url: `plus/custom-metadata/custom-field-definition/${id}`,
        method: "DELETE",
      }),
      invalidatesTags: ["Custom Field Definition", "Datamap"],
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
      transformResponse: (
        response: CustomFieldDefinitionWithId[] | { detail: string },
      ) => {
        if ("detail" in response) {
          return [];
        }
        return response.sort((a, b) =>
          (a.name ?? "").localeCompare(b.name ?? ""),
        );
      },
    }),
    getAllDictionaryEntries: build.query<Page_Vendor_, void>({
      query: () => ({
        params: { size: 2000 },
        url: `plus/dictionary/system`,
      }),
      providesTags: ["Dictionary"],
    }),
    getAllSystemVendors: build.query<DictSystems[], void>({
      query: () => ({
        url: `plus/dictionary/system-vendors`,
      }),
      providesTags: ["System Vendors"],
    }),
    postSystemVendors: build.mutation<any, string[]>({
      query: (vendor_ids: string[]) => ({
        method: "post",
        url: `plus/dictionary/system-vendors`,
        body: { vendor_ids },
      }),
      invalidatesTags: [
        "Dictionary",
        "System Vendors",
        "System",
        "Datamap",
        "System History",
        "Privacy Notices",
      ],
    }),
    getFidesCloudConfig: build.query<CloudConfig, void>({
      query: () => ({
        url: `plus/fides-cloud`,
        method: "GET",
      }),
      providesTags: ["Fides Cloud Config"],
    }),
    getSystemPurposeSummary: build.query<SystemPurposeSummary, string>({
      query: (fidesKey: string) => ({
        url: `plus/system/${fidesKey}/purpose-summary`,
        method: "GET",
      }),
      providesTags: ["System"],
    }),
    getVendorReport: build.query<
      Page_SystemSummary_,
      {
        pageIndex: number;
        pageSize: number;
        search?: string;
        purposes?: string;
        specialPurposes?: string;
        dataUses?: string;
        legalBasis?: string;
        consentCategories?: string;
      }
    >({
      query: ({
        pageIndex,
        pageSize,
        dataUses,
        search,
        legalBasis,
        purposes,
        specialPurposes,
        consentCategories,
      }) => {
        let queryString = `page=${pageIndex}&size=${pageSize}`;
        if (dataUses) {
          queryString += `&${dataUses}`;
        }

        if (legalBasis) {
          queryString += `&${legalBasis}`;
        }
        if (purposes) {
          queryString += `&${purposes}`;
        }
        if (specialPurposes) {
          queryString += `&${specialPurposes}`;
        }
        if (consentCategories) {
          queryString += `&${consentCategories}`;
        }

        if (search) {
          queryString += `&search=${search}`;
        }

        return {
          url: `plus/system/consent-management/report?${queryString}`,
          method: "GET",
        };
      },
      providesTags: ["System"],
    }),
    getDictionaryDataUses: build.query<
      Page_DataUseDeclaration_,
      { vendor_id: string }
    >({
      query: ({ vendor_id }) => ({
        params: { size: 1000 },
        url: `plus/dictionary/data-use-declarations/${vendor_id}`,
        method: "GET",
      }),
      providesTags: ["Dictionary"],
    }),
    getSystemHistory: build.query<
      Page_SystemHistoryResponse_,
      { system_key: string; page?: number; size?: number }
    >({
      query: (params) => ({
        url: `plus/system/${params.system_key}/history`,
        params: {
          page: params.page,
          size: params.size,
        },
      }),
      providesTags: () => ["System History"],
    }),
    updateCustomAsset: build.mutation<
      void,
      { assetType: CustomAssetType; file: File }
    >({
      query: ({ assetType, file }) => ({
        url: `plus/custom-asset/${assetType}`,
        method: "PUT",
        body: file,
        responseHandler: (response: { text: () => any }) => response.text(),
      }),
      invalidatesTags: () => ["Custom Assets"],
    }),
    patchPlusSystemConnectionConfigs: build.mutation<
      BulkPutConnectionConfiguration,
      {
        systemFidesKey: string;
        connectionConfigs: (Omit<
          ConnectionConfigurationResponse,
          "created_at"
        > & {
          enabled_actions?: string[];
        })[];
      }
    >({
      query: ({ systemFidesKey, connectionConfigs }) => ({
        url: `/plus/system/${systemFidesKey}/connection`,
        method: "PATCH",
        body: connectionConfigs,
      }),
      invalidatesTags: ["Datamap", "System", "Datastore Connection"],
    }),
    createPlusSaasConnectionConfig: build.mutation<
      CreateSaasConnectionConfigResponse,
      CreateSaasConnectionConfig
    >({
      query: (params) => {
        const url = `/plus/system/${params.systemFidesKey}${CONNECTION_ROUTE}/instantiate/${params.connectionConfig.saas_connector_type}`;

        return {
          url,
          method: "POST",
          body: { ...params.connectionConfig },
        };
      },
      // Creating a connection config also creates a dataset behind the scenes
      invalidatesTags: () => ["Datastore Connection", "Datasets", "System"],
    }),
    getTcfPurposeOverrides: build.query<TCFPurposeOverrideSchema[], void>({
      query: () => ({
        url: `plus/tcf/purpose_overrides`,
        method: "GET",
      }),
      providesTags: ["TCF Purpose Override"],
    }),
    patchTcfPurposeOverrides: build.mutation<
      TCFPurposeOverrideSchema[],
      TCFPurposeOverrideSchema[]
    >({
      query: (overrides) => ({
        url: `plus/tcf/purpose_overrides`,
        method: "PATCH",
        body: overrides,
      }),
      invalidatesTags: ["TCF Purpose Override"],
    }),
    getConsentableItems: build.query<ConsentableItem[], string>({
      query: (connectionKey) => ({
        url: `plus${CONNECTION_ROUTE}/${connectionKey}/consentable-items`,
      }),
      providesTags: () => ["Consentable Items"],
    }),
    updateConsentableItems: build.mutation<
      ConsentableItem[],
      { connectionKey: string; consentableItems: ConsentableItem[] }
    >({
      query: ({ connectionKey, consentableItems }) => ({
        url: `plus${CONNECTION_ROUTE}/${connectionKey}/consentable-items`,
        method: "PUT",
        body: consentableItems,
      }),
      invalidatesTags: ["Consentable Items"],
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
  useGetVendorReportQuery,
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
  useBulkUpdateCustomFieldsMutation,
  useGetAllCustomFieldDefinitionsQuery,
  useGetAllowListQuery,
  useGetAllDictionaryEntriesQuery,
  useGetFidesCloudConfigQuery,
  useGetDictionaryDataUsesQuery,
  useLazyGetDictionaryDataUsesQuery,
  useGetAllSystemVendorsQuery,
  usePostSystemVendorsMutation,
  useGetSystemHistoryQuery,
  useGetSystemPurposeSummaryQuery,
  useUpdateCustomAssetMutation,
  usePatchPlusSystemConnectionConfigsMutation,
  useCreatePlusSaasConnectionConfigMutation,
  useGetTcfPurposeOverridesQuery,
  usePatchTcfPurposeOverridesMutation,
  useGetConsentableItemsQuery,
  useUpdateConsentableItemsMutation,
} = plusApi;

export const selectHealth: (state: RootState) => HealthCheck | undefined =
  createSelector(plusApi.endpoints.getHealth.select(), ({ data }) => data);

export const selectDataFlowScannerStatus: (
  state: RootState,
) => SystemScannerStatus | undefined = createSelector(
  plusApi.endpoints.getHealth.select(),
  ({ data }) => data?.system_scanner,
);

const emptyClassifyInstances: ClassifyInstanceResponseValues[] = [];
export const selectDatasetClassifyInstances = createSelector(
  plusApi.endpoints.getAllClassifyInstances.select({
    resource_type: GenerateTypes.DATASETS,
  }),
  ({ data: instances }) => instances ?? emptyClassifyInstances,
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
  (instances) => instancesToMap(instances),
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
      : undefined,
);

const emptyCollectionMap: Map<string, ClassifyCollection> = new Map();
export const selectClassifyInstanceCollectionMap = createSelector(
  selectActiveClassifyDataset,
  (classifyInstance) =>
    classifyInstance?.collections
      ? new Map(classifyInstance.collections.map((c) => [c.name, c]))
      : emptyCollectionMap,
);
export const selectClassifyInstanceCollection = createSelector(
  [selectClassifyInstanceCollectionMap, selectActiveCollection],
  (collectionMap, active) =>
    active ? collectionMap.get(active.name) : undefined,
);

const emptyFieldMap: Map<string, ClassifyField> = new Map();
export const selectClassifyInstanceFieldMap = createSelector(
  selectClassifyInstanceCollection,
  (collection) =>
    collection?.fields
      ? new Map(collection.fields.map((f) => [f.name, f]))
      : emptyFieldMap,
);
/**
 * Note that this selects the field that is currently active in the editor. Fields that are shown in
 * the table are looked up by their name using selectClassifyInstanceFieldMap.
 */
export const selectClassifyInstanceField = createSelector(
  [selectClassifyInstanceFieldMap, selectActiveField],
  (fieldMap, active) => (active ? fieldMap.get(active.name) : undefined),
);

const emptySelectAllCustomFields: CustomFieldDefinitionWithId[] = [];
export const selectAllCustomFieldDefinitions = createSelector(
  plusApi.endpoints.getAllCustomFieldDefinitions.select(),
  ({ data }) => data || emptySelectAllCustomFields,
);

export type DictOption = {
  label: string;
  value: string;
  description?: string;
};

const EMPTY_DICT_ENTRIES: DictOption[] = [];
export const selectAllDictEntries = createSelector(
  [
    (RootState) => RootState,
    plusApi.endpoints.getAllDictionaryEntries.select(),
  ],
  (RootState, { data }) =>
    data
      ? data.items
          .map((d) => ({
            label: (d.name ?? d.legal_name) || "",
            value: d.vendor_id || "",
            description: d.description ? d.description : undefined,
          }))
          .sort((a, b) => (a.label > b.label ? 1 : -1))
      : EMPTY_DICT_ENTRIES,
);

const EMPTY_DICT_ENTRY = undefined;
export const selectDictEntry = (vendorId: string) =>
  createSelector(
    [(state) => state, plusApi.endpoints.getAllDictionaryEntries.select()],
    (state, { data }) => {
      const dictEntry = data?.items.find((d) => d.vendor_id === vendorId);

      return dictEntry || EMPTY_DICT_ENTRY;
    },
  );

const EMPTY_DATA_USES: DataUseDeclaration[] = [];

export const selectDictDataUses = (vendorId: string) =>
  createSelector(
    [
      (state) => state,
      plusApi.endpoints.getDictionaryDataUses.select({ vendor_id: vendorId }),
    ],
    (state, { data }) => (data ? data.items : EMPTY_DATA_USES),
  );

export type DictSystems = {
  linked_system: boolean;
  name: string;
  vendor_id: string;
};
const EMPTY_DICT_SYSTEMS: DictSystems[] = [];
export const selectAllDictSystems = createSelector(
  [(RootState) => RootState, plusApi.endpoints.getAllSystemVendors.select()],
  (RootState, { data }) =>
    data
      ? data
          .slice()
          .map((ds) => {
            const name = ds.name
              .split(" ")
              .map((word) =>
                word.charAt(0) === "("
                  ? `(${word.charAt(1).toUpperCase()}${word
                      .slice(2)
                      .toLowerCase()}`
                  : word.charAt(0).toUpperCase() + word.slice(1).toLowerCase(),
              )
              .join(" ");
            return {
              ...ds,
              name,
            };
          })
          .sort((a, b) => a.name.localeCompare(b.name))
      : EMPTY_DICT_SYSTEMS,
);
