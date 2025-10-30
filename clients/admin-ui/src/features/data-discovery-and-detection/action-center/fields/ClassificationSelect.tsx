import { AntButton as Button, Icons } from "fidesui";
import { useState } from "react";

import {
  TaxonomySelect,
  TaxonomySelectOption,
  TaxonomySelectProps,
} from "~/features/common/dropdown/TaxonomySelect";
import useTaxonomies from "~/features/common/hooks/useTaxonomies";

const ClassificationSelect = ({
  onSelectDataCategory,
  ...props
}: { onSelectDataCategory: (value: string) => void } & TaxonomySelectProps) => {
  const { getDataCategoryDisplayNameProps, getDataCategories } =
    useTaxonomies();
  const dataCategories = getDataCategories().filter((c) => c.active);
  const [open, setOpen] = useState(false);

  const options: TaxonomySelectOption[] = dataCategories.map((dataCategory) => {
    const { name, primaryName } = getDataCategoryDisplayNameProps(
      dataCategory.fides_key,
    );

    return {
      value: dataCategory.fides_key,
      label: (
        <div>
          <strong>{primaryName || name}</strong>
          {primaryName && `: ${name}`}
        </div>
      ),
      name,
      primaryName,
      description: dataCategory.description || "",
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
        onSelectDataCategory(value);
        setOpen(false);
      }}
      {...props}
    />
  );
};

export default ClassificationSelect;
