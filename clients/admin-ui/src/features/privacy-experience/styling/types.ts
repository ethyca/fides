export enum StylableCssPropertiesEnum {
  color = "color",
  fontSize = "font-size",
  fontWeight = "font-weight",
  backgroundColor = "background-color",
  backgroundSize = "background-size",
  backgroundImage = "background-image",
  backgroundRepeat = "background-repeat",
  backgroundPosition = "background-position",
  paddingTop = "padding-top",
  paddingBottom = "padding-bottom",
}

export type StylingOption = {
  id: string;
  label: string;
  cssSelector: string;
  properties: StylableCssPropertiesEnum[];
};
