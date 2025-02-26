import { useAppSelector } from "~/app/hooks";
import {
  selectDataSubjects,
  selectEnabledDataSubjects,
  useGetAllDataSubjectsQuery,
} from "~/features/data-subjects/data-subject.slice";
import {
  selectDataUses,
  selectEnabledDataUses,
  useGetAllDataUsesQuery,
} from "~/features/data-use/data-use.slice";
import {
  selectAllFilteredDatasets,
  useGetAllFilteredDatasetsQuery,
} from "~/features/dataset";
import {
  selectDataCategories,
  selectEnabledDataCategories,
  useGetAllDataCategoriesQuery,
} from "~/features/taxonomy";

/**
 * Set up subscriptions to all taxonomy resources.
 *
 * Conditionally subscribe to datasets, as not all privacy declarations need this field.
 */
export const usePrivacyDeclarationData = ({
  includeDatasets,
  includeDisabled,
}: {
  includeDatasets?: boolean;
  includeDisabled?: boolean;
}) => {
  // Query subscriptions:
  const { isLoading: isLoadingDataCategories } = useGetAllDataCategoriesQuery();
  const { isLoading: isLoadingDataSubjects } = useGetAllDataSubjectsQuery();
  const { isLoading: isLoadingDataUses } = useGetAllDataUsesQuery();
  const { isLoading: isLoadingDatasets } = useGetAllFilteredDatasetsQuery(
    {
      onlyUnlinkedDatasets: false,
    },
    {
      skip: !includeDatasets,
    },
  );

  const allDataCategories = useAppSelector(selectDataCategories);
  const enabledDataCategories = useAppSelector(selectEnabledDataCategories);
  const allDataSubjects = useAppSelector(selectDataSubjects);
  const enabledDataSubjects = useAppSelector(selectEnabledDataSubjects);
  const allDataUses = useAppSelector(selectDataUses);
  const enabledDataUses = useAppSelector(selectEnabledDataUses);
  const allDatasets = useAppSelector(selectAllFilteredDatasets);

  const isLoading =
    isLoadingDataCategories ||
    isLoadingDataSubjects ||
    isLoadingDataUses ||
    isLoadingDatasets;

  return {
    allDataCategories: includeDisabled
      ? allDataCategories
      : enabledDataCategories,
    allDataSubjects: includeDisabled ? allDataSubjects : enabledDataSubjects,
    allDataUses: includeDisabled ? allDataUses : enabledDataUses,
    allDatasets: includeDatasets ? allDatasets : undefined,
    isLoading,
  };
};
