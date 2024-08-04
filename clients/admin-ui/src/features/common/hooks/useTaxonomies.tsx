/* eslint-disable @typescript-eslint/no-use-before-define */
import { find } from "lodash";
import { ReactNode } from "react";

import { useAppSelector } from "~/app/hooks";
import {
  selectDataSubjects,
  useGetAllDataSubjectsQuery,
} from "~/features/data-subjects/data-subject.slice";
import {
  selectDataUses,
  useGetAllDataUsesQuery,
} from "~/features/data-use/data-use.slice";
import {
  selectDataCategories,
  useGetAllDataCategoriesQuery,
} from "~/features/taxonomy";

const useTaxonomies = () => {
  const { dataUses, dataCategories, dataSubjects, isLoading } = useData();

  const getPrimaryKey = (fidesLangKey: string, level = 1) => {
    const delimiter = ".";
    const tokens = fidesLangKey.split(delimiter).slice(0, level);
    return tokens.join(delimiter);
  };

  /**
   * getDataDisplayName
   * Used to convert a fideslang key for Data Use or Data Category into
   * a human-readable name with hierarchy. eg. functional.storage -> "Functional: Local Data Storage"
   * Data subjects has their own simpler function (getDataSubjectDisplayName) below.
   */
  const getDataDisplayName = (
    fidesLangKey: string,
    getDataFunction: (fidesLangKey: string) =>
      | {
          parent_key?: string;
          name?: string;
        }
      | undefined,
    primaryLevel = 1,
  ): string | JSX.Element => {
    const data = getDataFunction(fidesLangKey);
    if (!data) {
      // Fallback to return key without changes
      return fidesLangKey;
    }

    const primaryLevelData = getDataFunction(
      getPrimaryKey(fidesLangKey, primaryLevel),
    );

    const isChild = !!data.parent_key;

    if (!isChild || primaryLevelData?.name === data.name) {
      // must include a key since this function is used as an iterator
      return <strong key={fidesLangKey}>{data.name}</strong>;
    }

    return (
      // must include a key since this function is used as an iterator
      <span key={fidesLangKey}>
        <strong>{primaryLevelData?.name}:</strong> {data.name}
      </span>
    );
  };

  /*
    Data Uses
  */
  const getDataUses = () => dataUses;
  const getDataUseByKey = (dataUseKey: string) =>
    find(dataUses, { fides_key: dataUseKey });

  const getDataUseDisplayName = (dataUseKey: string): JSX.Element | string =>
    getDataDisplayName(dataUseKey, getDataUseByKey, 1);

  /*
    Data Categories
  */
  const getDataCategories = () => dataCategories;
  const getDataCategoryByKey = (dataCategoryKey: string) =>
    find(dataCategories, { fides_key: dataCategoryKey });
  const getDataCategoryDisplayName = (
    dataCategoryKey: string,
  ): JSX.Element | string =>
    getDataDisplayName(dataCategoryKey, getDataCategoryByKey, 2);

  /*
    Data Subjects
  */
  const getDataSubjects = () => dataSubjects;
  const getDataSubjectByKey = (dataSubjectKey: string) =>
    find(dataSubjects, { fides_key: dataSubjectKey });
  const getDataSubjectDisplayName = (dataSubjectKey: string): ReactNode => {
    const dataSubject = getDataSubjectByKey(dataSubjectKey);
    if (!dataSubject) {
      // Fallback to return key without changes
      return dataSubjectKey;
    }

    return dataSubject.name;
  };

  return {
    getDataUses,
    getDataUseByKey,
    getDataUseDisplayName,
    getDataCategories,
    getDataCategoryByKey,
    getDataCategoryDisplayName,
    getDataSubjects,
    getDataSubjectByKey,
    getDataSubjectDisplayName,
    getPrimaryKey,
    isLoading,
  };
};

const useData = () => {
  const { isLoading: isLoadingDataUses } = useGetAllDataUsesQuery();
  const dataUses = useAppSelector(selectDataUses);
  const { isLoading: isLoadingDataCategories } = useGetAllDataCategoriesQuery();
  const dataCategories = useAppSelector(selectDataCategories);
  const { isLoading: isLoadingDataSubjects } = useGetAllDataSubjectsQuery();
  const dataSubjects = useAppSelector(selectDataSubjects);

  const isLoading =
    isLoadingDataUses || isLoadingDataCategories || isLoadingDataSubjects;

  return { dataUses, dataSubjects, dataCategories, isLoading };
};

export default useTaxonomies;
