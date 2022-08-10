import { useUpdateDataUseMutation } from "../data-use/data-use.slice";
import {
  useGetAllDataCategoriesQuery,
  useUpdateDataCategoryMutation,
} from "./data-categories.slice";

export const useDataCategory = () => {
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

export const useDataUse = () => {
  const labels = {
    fides_key: "Data use",
    name: "Data use name",
    description: "Data use description",
    parent_key: "Parent data use",
  };

  const [edit] = useUpdateDataUseMutation();

  return { labels, edit };
};
