import { useAppSelector } from "~/app/hooks";
import {
  selectDataSubjects,
  useGetAllDataSubjectsQuery,
} from "~/features/data-subjects/data-subject.slice";
import {
  selectDataUses,
  useGetAllDataUsesQuery,
} from "~/features/data-use/data-use.slice";
import { selectAllDatasets, useGetAllDatasetsQuery } from "~/features/dataset";
import {
  selectDataCategories,
  useGetAllDataCategoriesQuery,
} from "~/features/taxonomy";

/**
 * Set up subscriptions to all taxonomy resources
 */
export const usePrivacyDeclarationData = () => {
  // Query subscriptions:
  const { isLoading: isLoadingDataCategories } = useGetAllDataCategoriesQuery();
  const { isLoading: isLoadingDataSubjects } = useGetAllDataSubjectsQuery();
  const { isLoading: isLoadingDataUses } = useGetAllDataUsesQuery();
  const { isLoading: isLoadingDatasets } = useGetAllDatasetsQuery();

  const allDataCategories = useAppSelector(selectDataCategories);
  const allDataSubjects = useAppSelector(selectDataSubjects);
  const allDataUses = useAppSelector(selectDataUses);
  const allDatasets = useAppSelector(selectAllDatasets);

  const isLoading =
    isLoadingDataCategories ||
    isLoadingDataSubjects ||
    isLoadingDataUses ||
    isLoadingDatasets;

  return {
    allDataCategories,
    allDataSubjects,
    allDataUses,
    allDatasets,
    isLoading,
  };
};
