import { useAppSelector } from "~/app/hooks";
import {
  TaxonomySelect,
  TaxonomySelectOption,
  TaxonomySelectProps,
} from "~/features/common/dropdown/TaxonomySelect";
import {
  selectSystemGroupsAsTaxonomyEntities,
  useGetAllSystemGroupsQuery,
} from "~/features/system/system-groups.slice";

const SystemGroupSelect = ({
  selectedTaxonomies,
  showDisabled = false,
  ...props
}: TaxonomySelectProps) => {
  useGetAllSystemGroupsQuery();
  const systemGroups = useAppSelector(selectSystemGroupsAsTaxonomyEntities);

  const visibleGroups = showDisabled
    ? systemGroups
    : systemGroups.filter((g) => g.active);

  const options: TaxonomySelectOption[] = visibleGroups
    .filter((group) => !selectedTaxonomies?.includes(group.fides_key))
    .map((group) => ({
      value: group.fides_key,
      name: group.name ?? group.fides_key,
      description: group.description ?? "",
      title: group.fides_key,
    }));

  return <TaxonomySelect options={options} {...props} />;
};

export default SystemGroupSelect;
