import { InputType } from "storybook/internal/csf";

import { InputProps } from "../../index";

const INPUT_VARIANT: Record<
  NonNullable<InputProps["variant"]>,
  InputProps["variant"]
> = {
  borderless: "borderless",
  outlined: "outlined",
  filled: "filled",
  underlined: "underlined",
};

export const inputVariantControl: InputType = {
  control: "select",
  options: Object.keys(INPUT_VARIANT),
};
