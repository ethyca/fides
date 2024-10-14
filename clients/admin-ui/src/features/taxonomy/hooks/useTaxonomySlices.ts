import {
  useDeleteDataSubjectMutation,
  useUpdateDataSubjectMutation,
} from "~/features/data-subjects/data-subject.slice";
import {
  useDeleteDataUseMutation,
  useUpdateDataUseMutation,
} from "~/features/data-use/data-use.slice";

import {
  useDeleteDataCategoryMutation,
  useUpdateDataCategoryMutation,
} from "../taxonomy.slice";
import { DefaultTaxonomyTypes } from "../types/DefaultTaxonomyTypes";

const useTaxonomySlices = ({
  taxonomyType,
}: {
  taxonomyType: DefaultTaxonomyTypes;
}) => {
  /* UPDATE */
  const [updateDataCategoryMutationTrigger] = useUpdateDataCategoryMutation();
  const [updateDataUseMutationTrigger] = useUpdateDataUseMutation();
  const [updateDataSubjectsMutationTrigger] = useUpdateDataSubjectMutation();

  /* DELETE  */
  const [deleteDataCategoryMutationTrigger] = useDeleteDataCategoryMutation();
  const [deleteDataUseMutationTrigger] = useDeleteDataUseMutation();
  const [deleteDataSubjectMutationTrigger] = useDeleteDataSubjectMutation();

  if (taxonomyType === "data_subjects") {
    return {
      updateTrigger: updateDataSubjectsMutationTrigger,
      deleteTrigger: deleteDataSubjectMutationTrigger,
    };
  }

  if (taxonomyType === "data_uses") {
    return {
      updateTrigger: updateDataUseMutationTrigger,
      deleteTrigger: deleteDataUseMutationTrigger,
    };
  }

  return {
    updateTrigger: updateDataCategoryMutationTrigger,
    deleteTrigger: deleteDataCategoryMutationTrigger,
  };
};
export default useTaxonomySlices;
