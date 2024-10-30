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
import { CoreTaxonomiesEnum } from "../types/CoreTaxonomiesEnum";

const useTaxonomySlices = ({
  taxonomyType,
}: {
  taxonomyType: CoreTaxonomiesEnum;
}) => {
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
      updateTrigger: updateDataSubjectsMutationTrigger,
      deleteTrigger: deleteDataSubjectMutationTrigger,
    };
  }

  if (taxonomyType === CoreTaxonomiesEnum.DATA_USES) {
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
