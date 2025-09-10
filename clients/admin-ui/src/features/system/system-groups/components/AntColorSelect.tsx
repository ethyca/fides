import { AntSelect as Select, AntSelectProps as SelectProps } from "fidesui";
import { HTMLAttributes } from "react";

import { COLOR_VALUE_MAP } from "~/features/system/system-groups/colors";
import { CustomTaxonomyColor } from "~/types/api";

import { COLOR_LABELS } from "./ColorSelect";

type AntColorSelectProps = Omit<SelectProps, "options">;

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

const AntColorSelect = (props: AntColorSelectProps) => {
  const options = (
    Object.values(CustomTaxonomyColor) as CustomTaxonomyColor[]
  ).map((value) => ({
    value,
    label: (
      <span className="flex items-center">
        <ColorSwatch color={value} />
        <span>{COLOR_LABELS[value]}</span>
      </span>
    ),
  }));

  return <Select {...props} options={options} placeholder="Select color" />;
};

export default AntColorSelect;
