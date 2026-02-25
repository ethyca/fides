import { InputType } from "storybook/internal/csf";

import { Icons } from "../../index";

export const iconControl: InputType = {
  control: "select",
  options: Object.keys(Icons),
  mapping: Object.fromEntries(
    Object.entries(Icons).map(([key, Component]) => {
      return [key, <Component key={key} />];
    }),
  ),
};
