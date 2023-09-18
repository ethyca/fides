import { Cookies, PrivacyDeclaration } from "~/types/api";

export interface MinimalPrivacyDeclaration {
  name: string;
  data_use: PrivacyDeclaration["data_use"];
  data_categories: PrivacyDeclaration["data_categories"];
  /**
   * Because we only allow inputting a string for cookies, we use cookieNames
   * to make the form easier to handle. However, we also keep the full `cookies`
   * object because the dictionary could potentially give us more than just the names
   * and we want a place to keep that information.
   */
  cookieNames: string[];
  cookies: Cookies[];
}

export interface FormValues {
  name: string;
  vendor_id?: string;
  privacy_declarations: MinimalPrivacyDeclaration[];
}

export const EMPTY_DECLARATION: MinimalPrivacyDeclaration = {
  name: "",
  data_use: "",
  // TODO(fides#4059): data categories will eventually be optional
  data_categories: ["user"],
  cookieNames: [],
  cookies: [],
};
