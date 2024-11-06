import {
  useCreateDataSubjectMutation,
  useDeleteDataSubjectMutation,
  useUpdateDataSubjectMutation,
} from "~/features/data-subjects/data-subject.slice";
import {
  useCreateDataUseMutation,
  useDeleteDataUseMutation,
  useUpdateDataUseMutation,
} from "~/features/data-use/data-use.slice";

import {
  useCreateDataCategoryMutation,
  useDeleteDataCategoryMutation,
  useUpdateDataCategoryMutation,
} from "../taxonomy.slice";
import { CoreTaxonomiesEnum } from "../types/CoreTaxonomiesEnum";

const useTaxonomySlices = ({
  taxonomyType,
}: {
  taxonomyType: CoreTaxonomiesEnum;
}) => {
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
      updateTrigger: updateDataSubjectsMutationTrigger,
      deleteTrigger: deleteDataSubjectMutationTrigger,
      createTrigger: createDataSubjectMutationTrigger,
    };
  }

  if (taxonomyType === CoreTaxonomiesEnum.DATA_USES) {
    return {
      updateTrigger: updateDataUseMutationTrigger,
      deleteTrigger: deleteDataUseMutationTrigger,
      createTrigger: createDataUseMutationTrigger,
    };
  }

  return {
    updateTrigger: updateDataCategoryMutationTrigger,
    deleteTrigger: deleteDataCategoryMutationTrigger,
    createTrigger: createDataCategoryMutationTrigger,
  };
};
export default useTaxonomySlices;
