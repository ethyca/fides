import { AntSelectProps } from "fidesui";

import { useFeatures } from "~/features/common/features";
import {
  CoreTaxonomiesEnum,
  TaxonomyTypeEnum,
} from "~/features/taxonomy/constants";
import { useGetCustomTaxonomiesQuery } from "~/features/taxonomy/taxonomy.slice";

const useCustomFieldValueTypeOptions = (
  includeCustomOption: boolean = true,
) => {
  const { plus: isPlusEnabled } = useFeatures();
  const { data: customTaxonomies, isLoading: isCustomTaxonomiesLoading } =
    useGetCustomTaxonomiesQuery(undefined as void, {
      skip: !isPlusEnabled,
    });
  const valueTypeOptions: AntSelectProps["options"] = [];

  if (includeCustomOption) {
    valueTypeOptions.push({ label: "Custom", value: "custom" });
  }

  valueTypeOptions.push(
    ...[
      {
        label: CoreTaxonomiesEnum.DATA_CATEGORIES,
        value: TaxonomyTypeEnum.DATA_CATEGORY,
      },
      {
        label: CoreTaxonomiesEnum.DATA_USES,
        value: TaxonomyTypeEnum.DATA_USE,
      },
      {
        label: CoreTaxonomiesEnum.DATA_SUBJECTS,
        value: TaxonomyTypeEnum.DATA_SUBJECT,
      },
    ],
  );

  if (isPlusEnabled) {
    valueTypeOptions.push({
      label: CoreTaxonomiesEnum.SYSTEM_GROUPS,
      value: TaxonomyTypeEnum.SYSTEM_GROUP,
    });
  }

  if (isCustomTaxonomiesLoading) {
    return { valueTypeOptions, customTaxonomies: [] };
  }

  if (customTaxonomies?.length) {
    valueTypeOptions.push(
      ...customTaxonomies.map((taxonomy) => ({
        label: taxonomy.name,
        value: taxonomy.fides_key,
      })),
    );
  }

  return { valueTypeOptions, customTaxonomies };
};

export default useCustomFieldValueTypeOptions;
