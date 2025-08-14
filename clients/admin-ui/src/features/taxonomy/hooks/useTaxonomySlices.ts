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
import { CoreTaxonomiesEnum } from "~/features/taxonomy/constants";
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

const taxonomyTypeToKey: Record<CoreTaxonomiesEnum, string | null> = {
  [CoreTaxonomiesEnum.DATA_CATEGORIES]: null,
  [CoreTaxonomiesEnum.DATA_USES]: null,
  [CoreTaxonomiesEnum.DATA_SUBJECTS]: null,
  [CoreTaxonomiesEnum.SYSTEM_GROUPS]: "system_group",
};

type TriggerFn = (...args: any[]) => any;
export type UseTaxonomySlicesResult = {
  getAllTrigger: TriggerFn;
  taxonomyItems: TaxonomyEntity[];
  updateTrigger: TriggerFn;
  deleteTrigger: TriggerFn;
  createTrigger: TriggerFn;
  isLoading: boolean;
  isError: boolean;
};

const useTaxonomySlices = ({
  taxonomyType,
}: {
  taxonomyType: CoreTaxonomiesEnum;
}): UseTaxonomySlicesResult => {
  /* GET ALL */
  const [getAllDataCategoriesQueryTrigger, dataCategoriesResult] =
    useLazyGetAllDataCategoriesQuery();
  const [getAllDataSubjectsQueryTrigger, dataSubjectsResult] =
    useLazyGetAllDataSubjectsQuery();
  const [getAllDataUsesQueryTrigger, dataUsesResult] =
    useLazyGetAllDataUsesQuery();

  /* CREATE */
  const [createDataCategoryMutationTrigger] = useCreateDataCategoryMutation();
  const [createDataUseMutationTrigger] = useCreateDataUseMutation();
  const [createDataSubjectMutationTrigger] = useCreateDataSubjectMutation();

  /* UPDATE */
  const [updateDataCategoryMutationTrigger] = useUpdateDataCategoryMutation();
  const [updateDataUseMutationTrigger] = useUpdateDataUseMutation();
  const [updateDataSubjectsMutationTrigger] = useUpdateDataSubjectMutation();

  /* DELETE  */
  const [deleteDataCategoryMutationTrigger] = useDeleteDataCategoryMutation();
  const [deleteDataUseMutationTrigger] = useDeleteDataUseMutation();
  const [deleteDataSubjectMutationTrigger] = useDeleteDataSubjectMutation();

  /* Generic taxonomy hooks */
  const [lazyGetTaxonomyTrigger, taxonomyResult] = useLazyGetTaxonomyQuery();
  const [createTaxonomyTrigger] = useCreateTaxonomyMutation();
  const [updateTaxonomyTrigger] = useUpdateTaxonomyMutation();
  const [deleteTaxonomyTrigger] = useDeleteTaxonomyMutation();

  const taxonomyKey = taxonomyTypeToKey[taxonomyType];

  // Stable callbacks for generic taxonomy
  const taxonomyGetAllTrigger = useCallback(() => {
    if (!taxonomyKey) {
      return Promise.resolve(undefined as any);
    }
    return lazyGetTaxonomyTrigger(taxonomyKey);
  }, [taxonomyKey, lazyGetTaxonomyTrigger]);

  const taxonomyCreateTrigger = useCallback(
    (payload: any) =>
      taxonomyKey
        ? createTaxonomyTrigger({ taxonomyType: taxonomyKey, ...payload })
        : Promise.resolve(undefined as any),
    [taxonomyKey, createTaxonomyTrigger],
  );

  const taxonomyUpdateTrigger = useCallback(
    (payload: any) =>
      taxonomyKey
        ? updateTaxonomyTrigger({ taxonomyType: taxonomyKey, ...payload })
        : Promise.resolve(undefined as any),
    [taxonomyKey, updateTaxonomyTrigger],
  );

  const taxonomyDeleteTrigger = useCallback(
    (key: string) =>
      taxonomyKey
        ? deleteTaxonomyTrigger({ taxonomyType: taxonomyKey, key })
        : Promise.resolve(undefined as any),
    [taxonomyKey, deleteTaxonomyTrigger],
  );

  // Data Categories
  if (taxonomyType === CoreTaxonomiesEnum.DATA_CATEGORIES) {
    return {
      getAllTrigger: getAllDataCategoriesQueryTrigger,
      taxonomyItems: dataCategoriesResult.data || [],
      updateTrigger: updateDataCategoryMutationTrigger,
      deleteTrigger: deleteDataCategoryMutationTrigger,
      createTrigger: createDataCategoryMutationTrigger,
      isLoading: dataCategoriesResult.isLoading,
      isError: dataCategoriesResult.isError,
    };
  }

  // Data Uses
  if (taxonomyType === CoreTaxonomiesEnum.DATA_USES) {
    return {
      getAllTrigger: getAllDataUsesQueryTrigger,
      taxonomyItems: dataUsesResult.data || [],
      updateTrigger: updateDataUseMutationTrigger,
      deleteTrigger: deleteDataUseMutationTrigger,
      createTrigger: createDataUseMutationTrigger,
      isLoading: dataUsesResult.isLoading,
      isError: dataUsesResult.isError,
    };
  }

  // Data Subjects
  if (taxonomyType === CoreTaxonomiesEnum.DATA_SUBJECTS) {
    return {
      getAllTrigger: getAllDataSubjectsQueryTrigger,
      taxonomyItems: dataSubjectsResult.data || [],
      updateTrigger: updateDataSubjectsMutationTrigger,
      deleteTrigger: deleteDataSubjectMutationTrigger,
      createTrigger: createDataSubjectMutationTrigger,
      isLoading: dataSubjectsResult.isLoading,
      isError: dataSubjectsResult.isError,
    };
  }

  // Generic taxonomies
  if (taxonomyKey) {
    return {
      getAllTrigger: taxonomyGetAllTrigger,
      taxonomyItems: taxonomyResult?.data || [],
      updateTrigger: taxonomyUpdateTrigger,
      deleteTrigger: taxonomyDeleteTrigger,
      createTrigger: taxonomyCreateTrigger,
      isLoading: taxonomyResult?.isLoading || false,
      isError: taxonomyResult?.isError || false,
    };
  }

  // Should be unreachable for known CoreTaxonomiesEnum values.
  throw new Error(`Unsupported taxonomy type: ${taxonomyType}`);
};

export default useTaxonomySlices;
