import { HTMLAttributes, useState } from "react";

import {
  ControlledSelect,
  ControlledSelectProps,
} from "~/features/common/form/ControlledSelect";
import { COLOR_VALUE_MAP } from "~/features/system/system-groups/colors";
import { CustomTaxonomyColor } from "~/types/api";

type ColorSelectProps = Omit<ControlledSelectProps, "options">;

export const COLOR_LABELS: Record<CustomTaxonomyColor, string> = {
  [CustomTaxonomyColor.TAXONOMY_WHITE]: "White",
  [CustomTaxonomyColor.TAXONOMY_RED]: "Red",
  [CustomTaxonomyColor.TAXONOMY_ORANGE]: "Orange",
  [CustomTaxonomyColor.TAXONOMY_YELLOW]: "Yellow",
  [CustomTaxonomyColor.TAXONOMY_GREEN]: "Green",
  [CustomTaxonomyColor.TAXONOMY_BLUE]: "Blue",
  [CustomTaxonomyColor.TAXONOMY_PURPLE]: "Purple",
  [CustomTaxonomyColor.SANDSTONE]: "Sandstone",
  [CustomTaxonomyColor.MINOS]: "Minos",
};

const ColorSwatch = ({
  color,
  ...props
}: { color: CustomTaxonomyColor } & HTMLAttributes<HTMLSpanElement>) => {
  return (
    <span
      aria-hidden
      className="mr-2 inline-block size-4 rounded-lg align-middle"
      style={{
        backgroundColor: `var(--fidesui-bg-${COLOR_VALUE_MAP[color]})`,
        border:
          color === CustomTaxonomyColor.TAXONOMY_WHITE
            ? "1px solid var(--fidesui-neutral-200)"
            : "none",
        ...props.style,
      }}
    />
  );
};

const renderColorOption = (option: any) => {
  const value = option?.value as CustomTaxonomyColor;
  const label = option?.label as string;
  return (
    <span className="flex items-center">
      <ColorSwatch color={value} />
      <span>{label}</span>
    </span>
  );
};

const ColorSelect = (props: ColorSelectProps) => {
  const options = (
    Object.values(CustomTaxonomyColor) as CustomTaxonomyColor[]
  ).map((value) => ({
    value,
    label: COLOR_LABELS[value],
  }));

  const [value, setValue] = useState<CustomTaxonomyColor | undefined>(
    undefined,
  );

  return (
    <ControlledSelect
      {...props}
      options={options}
      optionRender={renderColorOption}
      layout="stacked"
      value={value}
      onChange={(newValue) => {
        setValue(newValue as CustomTaxonomyColor);
      }}
      prefix={
        <ColorSwatch
          color={value ?? CustomTaxonomyColor.TAXONOMY_WHITE}
          style={{ marginBottom: "2px" }}
        />
      }
    />
  );
};

export default ColorSelect;
