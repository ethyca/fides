import {
  TaxonomyHookData,
  useDataCategory,
  useDataSubject,
  useDataUse,
} from "../hooks";
import { TaxonomyEntity } from "../types";
import { DefaultTaxonomyTypes } from "../types/DefaultTaxonomyTypes";

interface UseTaxonomyProps {
  taxonomyType: DefaultTaxonomyTypes;
}

const useTaxonomy = ({ taxonomyType }: UseTaxonomyProps) => {
  let hookData: TaxonomyHookData<TaxonomyEntity>;

  // Here we're using all of the taxonomy types hooks, so we're loading more data than we need
  // But, this could be replaced once we have generic endpoints that works for any taxonomy type

  const dataCategoryHookData = useDataCategory();
  const dataSubjectHookData = useDataSubject();
  const dataUseHookData = useDataUse();

  switch (taxonomyType) {
    case "data_categories":
      hookData = dataCategoryHookData;
      break;
    case "data_uses":
      hookData = dataUseHookData;
      break;
    case "data_subjects":
      hookData = dataSubjectHookData;
      break;
    default:
      break;
  }

  return {
    taxonomyItems: hookData!.data || [],
    ...hookData!,
  };
};
export default useTaxonomy;
