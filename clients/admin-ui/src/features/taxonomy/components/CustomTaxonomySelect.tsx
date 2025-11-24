import { AntSelect as Select, AntSelectProps as SelectProps } from "fidesui";

import { useGetTaxonomyQuery } from "~/features/taxonomy/taxonomy.slice";

interface CustomTaxonomySelectProps extends SelectProps {
  taxonomyKey: string;
}

const CustomTaxonomySelect = ({
  taxonomyKey,
  ...props
}: CustomTaxonomySelectProps) => {
  const { data: taxonomyItems, isLoading } = useGetTaxonomyQuery(taxonomyKey);

  if (!taxonomyItems) {
    return null;
  }

  return (
    <Select
      options={taxonomyItems.map((taxonomy) => ({
        value: taxonomy.fides_key,
        label: taxonomy.name ?? taxonomy.fides_key,
      }))}
      loading={isLoading}
      {...props}
    />
  );
};

export default CustomTaxonomySelect;
