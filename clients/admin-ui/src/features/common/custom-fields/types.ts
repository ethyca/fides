import { CustomFieldWithId } from "~/types/api";

import { TabData } from "../DataTabs";

export interface CustomFieldWithIdExtended extends CustomFieldWithId {
  allow_list_id?: string;
}

export interface Tab extends TabData {
  submitButtonText: string;
}
