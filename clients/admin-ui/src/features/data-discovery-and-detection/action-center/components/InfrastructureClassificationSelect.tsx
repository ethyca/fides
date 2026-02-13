import { Button, Icons } from "fidesui";
import { useState } from "react";

import {
  TaxonomySelect,
  TaxonomySelectOption,
  TaxonomySelectProps,
} from "~/features/common/dropdown/TaxonomySelect";
import useTaxonomies from "~/features/common/hooks/useTaxonomies";

const InfrastructureClassificationSelect = ({
  onSelectDataUse,
  urn,
  ...props
}: {
  onSelectDataUse: (value: string) => void;
  urn?: string;
} & TaxonomySelectProps) => {
  const { getDataUseDisplayNameProps, getDataUses } = useTaxonomies();
  const dataUses = getDataUses().filter((use) => use.active);
  const [open, setOpen] = useState(false);

  const options: TaxonomySelectOption[] = dataUses.map((dataUse) => {
    const { name, primaryName } = getDataUseDisplayNameProps(dataUse.fides_key);

    return {
      value: dataUse.fides_key,
      label: (
        <div>
          <strong>{primaryName || name}</strong>
          {primaryName && `: ${name}`}
        </div>
      ),
      name,
      primaryName,
      description: dataUse.description || "",
    };
  });
  return (
    <TaxonomySelect
      options={options}
      prefix={
        <Button
          aria-label="Add data use"
          type="text"
          size="small"
          icon={<Icons.Add />}
          disabled={props.disabled}
        />
      }
      placeholder=""
      suffixIcon={null}
      classNames={{
        root: "w-full max-w-full overflow-hidden p-0 cursor-pointer -ml-5",
      }}
      style={
        {
          "--ant-select-multiple-selector-bg-disabled": "transparent",
        } as React.CSSProperties
      }
      variant="borderless"
      autoFocus={false}
      maxTagCount="responsive"
      open={open}
      onOpenChange={(visible) => setOpen(visible)}
      onSelect={(value) => {
        onSelectDataUse(value);
        setOpen(false);
      }}
      data-classification-select={urn}
      popupMatchSelectWidth={600}
      {...props}
    />
  );
};

export default InfrastructureClassificationSelect;
