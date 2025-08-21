import { HTMLAttributes, useState } from "react";

import {
  ControlledSelect,
  ControlledSelectProps,
} from "~/features/common/form/ControlledSelect";

import { CustomTaxonomyColor } from "../types";

type ColorSelectProps = Omit<ControlledSelectProps, "options">;

const COLOR_LABELS: Record<CustomTaxonomyColor, string> = {
  [CustomTaxonomyColor.WHITE]: "White",
  [CustomTaxonomyColor.RED]: "Red",
  [CustomTaxonomyColor.ORANGE]: "Orange",
  [CustomTaxonomyColor.YELLOW]: "Yellow",
  [CustomTaxonomyColor.GREEN]: "Green",
  [CustomTaxonomyColor.BLUE]: "Blue",
  [CustomTaxonomyColor.PURPLE]: "Purple",
  [CustomTaxonomyColor.SANDSTONE]: "Sandstone",
  [CustomTaxonomyColor.MINOS]: "Minos",
};

const COLOR_VALUES: Record<CustomTaxonomyColor, string> = {
  [CustomTaxonomyColor.WHITE]: "var(--fidesui-bg-default)",
  [CustomTaxonomyColor.RED]: "var(--fidesui-bg-taxonomy-red)",
  [CustomTaxonomyColor.ORANGE]: "var(--fidesui-bg-taxonomy-orange)",
  [CustomTaxonomyColor.YELLOW]: "var(--fidesui-bg-taxonomy-yellow)",
  [CustomTaxonomyColor.GREEN]: "var(--fidesui-bg-taxonomy-green)",
  [CustomTaxonomyColor.BLUE]: "var(--fidesui-bg-taxonomy-blue)",
  [CustomTaxonomyColor.PURPLE]: "var(--fidesui-bg-taxonomy-purple)",
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
          color === COLOR_VALUES[CustomTaxonomyColor.WHITE]
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
          color={COLOR_VALUES[value ?? CustomTaxonomyColor.WHITE]}
          style={{ marginBottom: "2px" }}
        />
      }
    />
  );
};

export default ColorSelect;
