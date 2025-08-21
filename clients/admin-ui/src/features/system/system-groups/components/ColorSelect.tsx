import { HTMLAttributes, useState } from "react";

import {
  ControlledSelect,
  ControlledSelectProps,
} from "~/features/common/form/ControlledSelect";
import { CustomTaxonomyColor } from "~/types/api";

type ColorSelectProps = Omit<ControlledSelectProps, "options">;

const COLOR_LABELS: Record<CustomTaxonomyColor, string> = {
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

const COLOR_VALUES: Record<CustomTaxonomyColor, string> = {
  [CustomTaxonomyColor.TAXONOMY_WHITE]: "var(--fidesui-bg-default)",
  [CustomTaxonomyColor.TAXONOMY_RED]: "var(--fidesui-bg-taxonomy-red)",
  [CustomTaxonomyColor.TAXONOMY_ORANGE]: "var(--fidesui-bg-taxonomy-orange)",
  [CustomTaxonomyColor.TAXONOMY_YELLOW]: "var(--fidesui-bg-taxonomy-yellow)",
  [CustomTaxonomyColor.TAXONOMY_GREEN]: "var(--fidesui-bg-taxonomy-green)",
  [CustomTaxonomyColor.TAXONOMY_BLUE]: "var(--fidesui-bg-taxonomy-blue)",
  [CustomTaxonomyColor.TAXONOMY_PURPLE]: "var(--fidesui-bg-taxonomy-purple)",
  [CustomTaxonomyColor.SANDSTONE]: "var(--fidesui-bg-sandstone)",
  [CustomTaxonomyColor.MINOS]: "var(--fidesui-bg-minos)",
};

const ColorSwatch = ({
  color,
  ...props
}: { color: string } & HTMLAttributes<HTMLSpanElement>) => {
  return (
    <span
      aria-hidden
      className="mr-2 inline-block size-4 rounded-lg align-middle"
      style={{
        backgroundColor: color,
        border:
          color === COLOR_VALUES[CustomTaxonomyColor.TAXONOMY_WHITE]
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
  const color = COLOR_VALUES[value];
  return (
    <span className="flex items-center">
      <ColorSwatch color={color} />
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
          color={COLOR_VALUES[value ?? CustomTaxonomyColor.TAXONOMY_WHITE]}
          style={{ marginBottom: "2px" }}
        />
      }
    />
  );
};

export default ColorSelect;
