import { StylableCssPropertiesEnum, StylingOption } from "./types";

export const stylingOptionsAvailable: StylingOption[] = [
  {
    id: "title",
    label: "Title",
    cssSelector: ".heading-title",
    properties: [
      StylableCssPropertiesEnum.color,
      StylableCssPropertiesEnum.fontSize,
      StylableCssPropertiesEnum.fontWeight,
    ],
  },
  {
    id: "description",
    label: "Description",
    cssSelector: ".heading-description",
    properties: [
      StylableCssPropertiesEnum.color,
      StylableCssPropertiesEnum.fontSize,
      StylableCssPropertiesEnum.fontWeight,
    ],
  },
];

export const StylableCssPropertiesLabels = {
  [StylableCssPropertiesEnum.color]: "Color",
  [StylableCssPropertiesEnum.fontSize]: "Font size",
  [StylableCssPropertiesEnum.fontWeight]: "Font weight",
  [StylableCssPropertiesEnum.backgroundColor]: "Background color",
  [StylableCssPropertiesEnum.backgroundSize]: "Background size",
  [StylableCssPropertiesEnum.backgroundImage]: "Background image",
  [StylableCssPropertiesEnum.paddingX]: "Horizontal padding",
  [StylableCssPropertiesEnum.paddingY]: "Vertical padding",
};

export const sizeOptions = [
  {
    label: "Small",
    value: "12px",
  },
  {
    label: "Medium",
    value: "16px",
  },
  {
    label: "Large",
    value: "20px",
  },
];
