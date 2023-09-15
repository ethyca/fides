import { PrivacyDeclaration } from "~/types/api";

export interface MinimalPrivacyDeclaration {
  name: string;
  data_use: PrivacyDeclaration["data_use"];
  data_categories: PrivacyDeclaration["data_categories"];
  cookies: string[];
}

export interface FormValues {
  name: string;
  vendor_id?: string;
  privacy_declarations: MinimalPrivacyDeclaration[];
}

export const EMPTY_DECLARATION: MinimalPrivacyDeclaration = {
  name: "",
  data_use: "",
  data_categories: ["user"],
  cookies: [],
};
