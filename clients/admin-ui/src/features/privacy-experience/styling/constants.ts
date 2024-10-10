import { S } from "msw/lib/glossary-de6278a9";

import { StylableCssPropertiesEnum, StylingOption } from "./types";

export const stylingOptionsAvailable: StylingOption[] = [
  {
    id: "header",
    label: "Header",
    cssSelector: ".header",
    properties: [
      StylableCssPropertiesEnum.backgroundColor,
      StylableCssPropertiesEnum.paddingTop,
      StylableCssPropertiesEnum.paddingBottom,
    ],
  },
  {
    id: "page",
    label: "Page",
    cssSelector: "body",
    properties: [
      StylableCssPropertiesEnum.backgroundColor,
      StylableCssPropertiesEnum.backgroundImage,
      StylableCssPropertiesEnum.backgroundSize,
      StylableCssPropertiesEnum.backgroundRepeat,
      StylableCssPropertiesEnum.backgroundPosition,
    ],
  },
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
  [StylableCssPropertiesEnum.color]: "Text color",
  [StylableCssPropertiesEnum.fontSize]: "Font size",
  [StylableCssPropertiesEnum.fontWeight]: "Font weight",
  [StylableCssPropertiesEnum.backgroundColor]: "Background color",
  [StylableCssPropertiesEnum.backgroundSize]: "Background size",
  [StylableCssPropertiesEnum.backgroundImage]: "Background image",
  [StylableCssPropertiesEnum.backgroundRepeat]: "Background repeat",
  [StylableCssPropertiesEnum.backgroundPosition]: "Background position",
  [StylableCssPropertiesEnum.paddingTop]: "Padding top",
  [StylableCssPropertiesEnum.paddingBottom]: "Padding bottom",
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
