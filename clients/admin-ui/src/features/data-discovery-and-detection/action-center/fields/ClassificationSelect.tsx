import { AntButton as Button, Icons } from "fidesui";
import { useState } from "react";

import {
  TaxonomySelect,
  TaxonomySelectOption,
  TaxonomySelectProps,
} from "~/features/common/dropdown/TaxonomySelect";
import useTaxonomies from "~/features/common/hooks/useTaxonomies";

const ClassificationSelect = ({ ...props }: TaxonomySelectProps) => {
  const { getDataUseDisplayNameProps, getDataUses } = useTaxonomies();
  const dataUses = getDataUses();
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
          aria-label="Add Data Category"
          type="text"
          size="small"
          icon={<Icons.Add />}
        />
      }
      placeholder=""
      suffixIcon={null}
      classNames={{
        root: "w-full max-w-full overflow-hidden p-0 cursor-pointer",
      }}
      variant="borderless"
      autoFocus={false}
      maxTagCount="responsive"
      open={open}
      onOpenChange={(visible) => setOpen(visible)}
      onSelect={(value, option) => {
        if (props.onSelect) {
          props.onSelect(value, option);
        }
        setOpen(false);
      }}
      {...props}
    />
  );
};

export default ClassificationSelect;
