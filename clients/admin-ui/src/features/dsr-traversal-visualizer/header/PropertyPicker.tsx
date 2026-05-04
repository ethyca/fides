import { Select } from "fidesui";
import { useMemo } from "react";

import { useGetAllPropertiesQuery } from "~/features/properties/property.slice";

interface Props {
  value: string | null;
  onChange: (propertyKey: string) => void;
}

const PropertyPicker = ({ value, onChange }: Props) => {
  const { data, isLoading } = useGetAllPropertiesQuery({ size: 100 });

  const options = useMemo(
    () =>
      (data?.items ?? []).map((p) => ({
        label: p.name,
        value: p.id ?? "",
      })),
    [data],
  );

  return (
    <Select
      data-testid="property-picker"
      aria-label="Select a property"
      showSearch
      placeholder="Select a property"
      style={{ minWidth: 240 }}
      value={value ?? undefined}
      loading={isLoading}
      options={options}
      onChange={onChange}
      optionFilterProp="label"
    />
  );
};

export default PropertyPicker;
