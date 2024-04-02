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

const useFidesLang = () => {
  const { dataUses, dataCategories, dataSubjects } = fetchData();

  const getTopLevelKey = (fidesLangKey: string) => {
    return fidesLangKey.split(".")[0];
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
      | undefined
  ): string | ReactNode => {
    const data = getDataFunction(fidesLangKey);
    if (!data) {
      // Fallback to return key without changes
      return fidesLangKey;
    }

    const isChild = !!data?.parent_key;
    if (!isChild) {
      return <strong>{data.name}</strong>;
    }

    const topLevelData = getDataFunction(getTopLevelKey(fidesLangKey));
    return (
      <span>
        <strong>{topLevelData?.name}:</strong> {data.name}
      </span>
    );
  };

  /* 
    Data Uses 
  */
  const getDataUses = () => dataUses;
  const getDataUseByKey = (dataUseKey: string) =>
    find(dataUses, { fides_key: dataUseKey });

  const getDataUseDisplayName = (dataUseKey: string): ReactNode =>
    getDataDisplayName(dataUseKey, getDataUseByKey);

  /* 
    Data Categories 
  */
  const getDataCategories = () => dataCategories;
  const getDataCategoryByKey = (dataCategoryKey: string) =>
    find(dataCategories, { fides_key: dataCategoryKey });
  const getDataCategoryDisplayName = (dataCategoryKey: string): ReactNode =>
    getDataDisplayName(dataCategoryKey, getDataCategoryByKey);

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
  };
};

const fetchData = () => {
  useGetAllDataUsesQuery();
  const dataUses = useAppSelector(selectDataUses);
  useGetAllDataSubjectsQuery();
  const dataSubjects = useAppSelector(selectDataSubjects);
  useGetAllDataCategoriesQuery();
  const dataCategories = useAppSelector(selectDataCategories);

  return { dataUses, dataSubjects, dataCategories };
};

export default useFidesLang;
