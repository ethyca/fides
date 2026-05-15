import { SelectProps } from "fidesui";

import {
  TaxonomySelect,
  TaxonomySelectOption,
} from "~/features/common/dropdown/TaxonomySelect";
import { useGetTaxonomyQuery } from "~/features/taxonomy/taxonomy.slice";

interface CustomTaxonomySelectProps extends Omit<
  SelectProps,
  "options" | "mode"
> {
  taxonomyKey: string;
  /** Same semantics as the other TaxonomySelect wrappers. */
  selectedTaxonomies?: string[];
  showDisabled?: boolean;
  /**
   * Pass-through to TaxonomySelect. Allowed values mirror Antd's single-select
   * (undefined) and multi-select ("multiple").
   */
  mode?: "multiple";
}

const CustomTaxonomySelect = ({
  taxonomyKey,
  selectedTaxonomies,
  showDisabled = false,
  ...props
}: CustomTaxonomySelectProps) => {
  const { data: taxonomyItems = [], isLoading } =
    useGetTaxonomyQuery(taxonomyKey);

  const visibleItems = showDisabled
    ? taxonomyItems
    : taxonomyItems.filter((t) => t.active !== false);

  const options: TaxonomySelectOption[] = visibleItems
    .filter((item) => !selectedTaxonomies?.includes(item.fides_key))
    .map((item) => ({
      value: item.fides_key,
      name: item.name ?? item.fides_key,
      description: item.description ?? "",
      title: item.fides_key,
    }));

  // TaxonomySelect props are a discriminated union (single vs multi mode);
  // CustomTaxonomySelect's flat prop shape can satisfy either branch at the
  // call site, so we cast to `any` here to keep the wrapper consumer-friendly.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const passthrough = props as any;

  return (
    <TaxonomySelect options={options} loading={isLoading} {...passthrough} />
  );
};

export default CustomTaxonomySelect;
