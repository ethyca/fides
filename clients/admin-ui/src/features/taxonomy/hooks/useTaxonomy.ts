import {
  TaxonomyHookData,
  useDataCategory,
  useDataSubject,
  useDataUse,
} from "../hooks";
import { TaxonomyEntity } from "../types";
import { CoreTaxonomiesEnum } from "../types/CoreTaxonomiesEnum";

interface UseTaxonomyProps {
  taxonomyType: CoreTaxonomiesEnum;
}

const useTaxonomy = ({ taxonomyType }: UseTaxonomyProps) => {
  let hookData: TaxonomyHookData<TaxonomyEntity>;

  // Here we're using all of the taxonomy types hooks, so we're loading more data than we need
  // But, this could be replaced once we have generic endpoints that works for any taxonomy type

  const dataCategoryHookData = useDataCategory();
  const dataSubjectHookData = useDataSubject();
  const dataUseHookData = useDataUse();

  switch (taxonomyType) {
    case CoreTaxonomiesEnum.DATA_CATEGORIES:
      hookData = dataCategoryHookData;
      break;
    case CoreTaxonomiesEnum.DATA_USES:
      hookData = dataUseHookData;
      break;
    case CoreTaxonomiesEnum.DATA_SUBJECTS:
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
