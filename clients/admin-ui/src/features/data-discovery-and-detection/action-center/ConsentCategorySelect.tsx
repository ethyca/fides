import { AntSpace as Space, Icons, SparkleIcon } from "fidesui";
import { useMemo } from "react";

import {
  TaxonomySelect,
  TaxonomySelectOption,
  TaxonomySelectOptions,
  TaxonomySelectProps,
} from "~/features/common/dropdown/TaxonomySelect";
import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import { CONSENT_CATEGORIES } from "~/features/data-discovery-and-detection/action-center/utils/isConsentCategory";

const ConsentCategorySelect = ({
  selectedTaxonomies,
  ...props
}: TaxonomySelectProps) => {
  const { getDataUseDisplayNameProps, getDataUses } = useTaxonomies();
  const dataUses = getDataUses();
  const filteredDataUses = [...dataUses]
    .filter((use) => !selectedTaxonomies?.includes(use.fides_key))
    .sort();
  const consentCategories = filteredDataUses.filter(
    (use) => use.active && CONSENT_CATEGORIES.includes(use.fides_key),
  );

  const options: TaxonomySelectOption[] = filteredDataUses.map((dataUse) => {
    const { name, primaryName } = getDataUseDisplayNameProps(dataUse.fides_key);
    return {
      value: dataUse.fides_key,
      name,
      primaryName,
      description: dataUse.description || "",
    };
  });

  const optionsGroups = useMemo(() => {
    const suggestedOptions: TaxonomySelectOption[] = [];
    const allOptions: TaxonomySelectOption[] = [];
    options.forEach((opt) => {
      if (
        consentCategories.some((category) => category.fides_key === opt.value)
      ) {
        suggestedOptions.push(opt);
      } else {
        allOptions.push(opt);
      }
    });
    return {
      suggested: suggestedOptions,
      all: allOptions,
    };
  }, [options, consentCategories]);

  const optionsToRender: TaxonomySelectOptions = optionsGroups.suggested.length
    ? [
        {
          label: (
            <Space>
              <SparkleIcon size={14} />
              <span>Categories of consent</span>
              <em className="font-normal">Recommended</em>
            </Space>
          ),
          options: optionsGroups.suggested,
        },
        {
          label: (
            <Space>
              <Icons.Document />
              <span>Other data uses</span>
            </Space>
          ),
          options: optionsGroups.all,
        },
      ]
    : optionsGroups.all;

  return <TaxonomySelect options={optionsToRender} {...props} />;
};

export default ConsentCategorySelect;
