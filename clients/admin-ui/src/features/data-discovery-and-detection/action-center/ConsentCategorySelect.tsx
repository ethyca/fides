import {
  TaxonomySelect,
  TaxonomySelectOption,
  TaxonomySelectProps,
} from "~/features/common/dropdown/TaxonomySelect";
import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import { CONSENT_CATEGORIES } from "~/features/data-discovery-and-detection/action-center/utils/isConsentCategory";

const ConsentCategorySelect = ({
  selectedTaxonomies,
  ...props
}: TaxonomySelectProps) => {
  const { getDataUseDisplayNameProps, getDataUses } = useTaxonomies();
  const consentCategories = getDataUses().filter(
    (use) => use.active && CONSENT_CATEGORIES.includes(use.fides_key),
  );

  const options: TaxonomySelectOption[] = consentCategories.map(
    (consentCategory) => {
      const { name, primaryName } = getDataUseDisplayNameProps(
        consentCategory.fides_key,
      );
      return {
        value: consentCategory.fides_key,
        name,
        primaryName,
        description: consentCategory.description || "",
      };
    },
  );
  return <TaxonomySelect options={options} {...props} />;
};

export default ConsentCategorySelect;
