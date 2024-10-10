export enum StylableCssPropertiesEnum {
  color = "color",
  fontSize = "font-size",
  fontWeight = "font-weight",
  backgroundColor = "background-color",
  backgroundSize = "background-size",
  backgroundImage = "background-image",
  paddingX = "paddingX",
  paddingY = "paddingY",
}

export type StylingOption = {
  id: string;
  label: string;
  cssSelector: string;
  properties: StylableCssPropertiesEnum[];
};
