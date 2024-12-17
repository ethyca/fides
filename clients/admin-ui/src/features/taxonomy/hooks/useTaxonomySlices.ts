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

import { CoreTaxonomiesEnum } from "../constants";
import {
  useCreateDataCategoryMutation,
  useDeleteDataCategoryMutation,
  useLazyGetAllDataCategoriesQuery,
  useUpdateDataCategoryMutation,
} from "../taxonomy.slice";

const useTaxonomySlices = ({
  taxonomyType,
}: {
  taxonomyType: CoreTaxonomiesEnum;
}) => {
  /* GET ALL (LAZY) */
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

  if (taxonomyType === CoreTaxonomiesEnum.DATA_SUBJECTS) {
    return {
      getAllTrigger: getAllDataSubjectsQueryTrigger,
      taxonomyItems: dataSubjectsResult.data || [],
      updateTrigger: updateDataSubjectsMutationTrigger,
      deleteTrigger: deleteDataSubjectMutationTrigger,
      createTrigger: createDataSubjectMutationTrigger,
    };
  }

  if (taxonomyType === CoreTaxonomiesEnum.DATA_USES) {
    return {
      getAllTrigger: getAllDataUsesQueryTrigger,
      taxonomyItems: dataUsesResult.data || [],
      updateTrigger: updateDataUseMutationTrigger,
      deleteTrigger: deleteDataUseMutationTrigger,
      createTrigger: createDataUseMutationTrigger,
    };
  }

  return {
    getAllTrigger: getAllDataCategoriesQueryTrigger,
    taxonomyItems: dataCategoriesResult.data || [],
    updateTrigger: updateDataCategoryMutationTrigger,
    deleteTrigger: deleteDataCategoryMutationTrigger,
    createTrigger: createDataCategoryMutationTrigger,
  };
};
export default useTaxonomySlices;
