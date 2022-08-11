import {
  useGetAllDataQualifiersQuery,
  useUpdateDataQualifierMutation,
} from "../data-qualifier/data-qualifier.slice";
import {
  useGetAllDataSubjectsQuery,
  useUpdateDataSubjectMutation,
} from "../data-subjects/data-subject.slice";
import {
  useGetAllDataUsesQuery,
  useUpdateDataUseMutation,
} from "../data-use/data-use.slice";
import {
  useGetAllDataCategoriesQuery,
  useUpdateDataCategoryMutation,
} from "./data-categories.slice";
import { TaxonomyEntity } from "./types";

export interface TaxonomyHookData {
  data?: TaxonomyEntity[];
  isLoading: boolean;
  labels: Labels;
  edit: (entity: TaxonomyEntity) => void;
}

interface Labels {
  fides_key: string;
  name: string;
  description: string;
  parent_key: string;
}

export const useDataCategory = (): TaxonomyHookData => {
  const { data, isLoading } = useGetAllDataCategoriesQuery();

  const labels = {
    fides_key: "Data category",
    name: "Category name",
    description: "Category description",
    parent_key: "Parent category",
  };

  const [edit] = useUpdateDataCategoryMutation();

  return { data, isLoading, labels, edit };
};

export const useDataUse = (): TaxonomyHookData => {
  const { data, isLoading } = useGetAllDataUsesQuery();

  const labels = {
    fides_key: "Data use",
    name: "Data use name",
    description: "Data use description",
    parent_key: "Parent data use",
  };

  const [edit] = useUpdateDataUseMutation();

  return { data, isLoading, labels, edit };
};

export const useDataSubject = (): TaxonomyHookData => {
  const { data, isLoading } = useGetAllDataSubjectsQuery();

  const labels = {
    fides_key: "Data subject",
    name: "Data subject name",
    description: "Data subject description",
    parent_key: "Parent data subject",
  };

  const [edit] = useUpdateDataSubjectMutation();

  return { data, isLoading, labels, edit };
};

export const useDataQualifier = (): TaxonomyHookData => {
  const { data, isLoading } = useGetAllDataQualifiersQuery();

  const labels = {
    fides_key: "Data qualifier",
    name: "Data qualifier name",
    description: "Data qualifier description",
    parent_key: "Parent data qualifier",
  };

  const [edit] = useUpdateDataQualifierMutation();

  return { data, isLoading, labels, edit };
};
