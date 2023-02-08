import { ConsentValue } from "./consent-value";

export type ConsentOption = {
  cookieKeys: string[];
  default?: ConsentValue;
  fidesDataUseKey: string;
};

export type ConsentConfig = {
  options: ConsentOption[];
};
