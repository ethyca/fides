import { useCallback } from "react";

import {
  useCreateDataSubjectMutation,
  useDeleteDataSubjectMutation,
  useLazyGetAllDataSubjectsQuery,
  useUpdateDataSubjectMutation,
} from "~/features/data-subjects/data-subject.slice";
import {
  useCreateDataUseMutation,
  useDeleteDataUseMutation,
  useLazyGetAllDataUsesQuery,
  useUpdateDataUseMutation,
} from "~/features/data-use/data-use.slice";
import {
  useCreateSystemGroupMutation,
  useDeleteSystemGroupMutation,
  useLazyGetAllSystemGroupsQuery,
  useUpdateSystemGroupMutation,
} from "~/features/system/system-groups.slice";
import { TaxonomyTypeEnum } from "~/features/taxonomy/constants";
import {
  useCreateDataCategoryMutation,
  useDeleteDataCategoryMutation,
  useLazyGetAllDataCategoriesQuery,
  useUpdateDataCategoryMutation,
} from "~/features/taxonomy/data-category.slice";
import {
  useCreateTaxonomyMutation,
  useDeleteTaxonomyMutation,
  useLazyGetTaxonomyQuery,
  useUpdateTaxonomyMutation,
} from "~/features/taxonomy/taxonomy.slice";
import { TaxonomyEntity } from "~/features/taxonomy/types";

type TriggerFn = (...args: any[]) => any;
export type UseTaxonomySlicesResult = {
  getAllTrigger: TriggerFn;
  taxonomyItems: TaxonomyEntity[];
  updateTrigger: TriggerFn;
  deleteTrigger: TriggerFn;
  createTrigger: TriggerFn;
  isLoading: boolean;
  isError: boolean;
  isCreating: boolean;
};

const useTaxonomySlices = ({
  taxonomyType,
}: {
  taxonomyType: string; // fides_key of taxonomy
}): UseTaxonomySlicesResult => {
  /* GET ALL */
  const [getAllDataCategoriesQueryTrigger, dataCategoriesResult] =
    useLazyGetAllDataCategoriesQuery();
  const [getAllDataSubjectsQueryTrigger, dataSubjectsResult] =
    useLazyGetAllDataSubjectsQuery();
  const [getAllDataUsesQueryTrigger, dataUsesResult] =
    useLazyGetAllDataUsesQuery();
  const [getAllSystemGroupsQueryTrigger, systemGroupsResult] =
    useLazyGetAllSystemGroupsQuery();

  /* CREATE */
  const [createDataCategoryMutationTrigger, createDataCategoryResult] =
    useCreateDataCategoryMutation();
  const [createDataUseMutationTrigger, createDataUseResult] =
    useCreateDataUseMutation();
  const [createDataSubjectMutationTrigger, createDataSubjectResult] =
    useCreateDataSubjectMutation();
  const [createSystemGroupMutationTrigger, createSystemGroupResult] =
    useCreateSystemGroupMutation();

  /* UPDATE */
  const [updateDataCategoryMutationTrigger] = useUpdateDataCategoryMutation();
  const [updateDataUseMutationTrigger] = useUpdateDataUseMutation();
  const [updateDataSubjectsMutationTrigger] = useUpdateDataSubjectMutation();
  const [updateSystemGroupMutationTrigger] = useUpdateSystemGroupMutation();

  /* DELETE  */
  const [deleteDataCategoryMutationTrigger] = useDeleteDataCategoryMutation();
  const [deleteDataUseMutationTrigger] = useDeleteDataUseMutation();
  const [deleteDataSubjectMutationTrigger] = useDeleteDataSubjectMutation();
  const [deleteSystemGroupMutationTrigger] = useDeleteSystemGroupMutation();

  /* Generic taxonomy hooks */
  const [lazyGetTaxonomyTrigger, taxonomyResult] = useLazyGetTaxonomyQuery();
  const [createTaxonomyTrigger, createTaxonomyResult] =
    useCreateTaxonomyMutation();
  const [updateTaxonomyTrigger] = useUpdateTaxonomyMutation();
  const [deleteTaxonomyTrigger] = useDeleteTaxonomyMutation();

  // Stable callbacks for generic taxonomy
  const taxonomyGetAllTrigger = useCallback(() => {
    if (!taxonomyType) {
      return Promise.resolve(undefined as any);
    }
    return lazyGetTaxonomyTrigger(taxonomyType);
  }, [taxonomyType, lazyGetTaxonomyTrigger]);

  const taxonomyCreateTrigger = useCallback(
    (payload: any) =>
      taxonomyType
        ? createTaxonomyTrigger({ taxonomyType, ...payload })
        : Promise.resolve(undefined as any),
    [taxonomyType, createTaxonomyTrigger],
  );

  const taxonomyUpdateTrigger = useCallback(
    (payload: any) =>
      taxonomyType
        ? updateTaxonomyTrigger({ taxonomyType, ...payload })
        : Promise.resolve(undefined as any),
    [taxonomyType, updateTaxonomyTrigger],
  );

  const taxonomyDeleteTrigger = useCallback(
    (key: string) =>
      taxonomyType
        ? deleteTaxonomyTrigger({ taxonomyType, key })
        : Promise.resolve(undefined as any),
    [taxonomyType, deleteTaxonomyTrigger],
  );

  // Legacy core taxonomies using dedicated endpoints
  if (taxonomyType === TaxonomyTypeEnum.DATA_CATEGORY) {
    return {
      getAllTrigger: getAllDataCategoriesQueryTrigger,
      taxonomyItems: dataCategoriesResult.data || [],
      updateTrigger: updateDataCategoryMutationTrigger,
      deleteTrigger: deleteDataCategoryMutationTrigger,
      createTrigger: createDataCategoryMutationTrigger,
      isLoading: dataCategoriesResult.isLoading,
      isError: dataCategoriesResult.isError,
      isCreating: createDataCategoryResult.isLoading,
    };
  }

  // Data Uses
  if (taxonomyType === TaxonomyTypeEnum.DATA_USE) {
    return {
      getAllTrigger: getAllDataUsesQueryTrigger,
      taxonomyItems: dataUsesResult.data || [],
      updateTrigger: updateDataUseMutationTrigger,
      deleteTrigger: deleteDataUseMutationTrigger,
      createTrigger: createDataUseMutationTrigger,
      isLoading: dataUsesResult.isLoading,
      isError: dataUsesResult.isError,
      isCreating: createDataUseResult.isLoading,
    };
  }

  // Data Subjects
  if (taxonomyType === TaxonomyTypeEnum.DATA_SUBJECT) {
    return {
      getAllTrigger: getAllDataSubjectsQueryTrigger,
      taxonomyItems: dataSubjectsResult.data || [],
      updateTrigger: updateDataSubjectsMutationTrigger,
      deleteTrigger: deleteDataSubjectMutationTrigger,
      createTrigger: createDataSubjectMutationTrigger,
      isLoading: dataSubjectsResult.isLoading,
      isError: dataSubjectsResult.isError,
      isCreating: createDataSubjectResult.isLoading,
    };
  }

  // System Groups
  if (taxonomyType === TaxonomyTypeEnum.SYSTEM_GROUP) {
    return {
      getAllTrigger: getAllSystemGroupsQueryTrigger,
      taxonomyItems: systemGroupsResult.data || [],
      updateTrigger: updateSystemGroupMutationTrigger,
      deleteTrigger: deleteSystemGroupMutationTrigger,
      createTrigger: createSystemGroupMutationTrigger,
      isLoading: systemGroupsResult.isLoading,
      isError: systemGroupsResult.isError,
      isCreating: createSystemGroupResult.isLoading,
    };
  }

  // Generic taxonomies
  return {
    getAllTrigger: taxonomyGetAllTrigger,
    taxonomyItems: taxonomyResult?.data || [],
    updateTrigger: taxonomyUpdateTrigger,
    deleteTrigger: taxonomyDeleteTrigger,
    createTrigger: taxonomyCreateTrigger,
    isLoading: taxonomyResult?.isLoading || false,
    isError: taxonomyResult?.isError || false,
    isCreating: createTaxonomyResult.isLoading,
  };
};

export default useTaxonomySlices;
