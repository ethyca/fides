import { TreeResourceChangeIndicator } from "~/types/api";
import { FieldActionType } from "~/types/api/models/FieldActionType";

export const ALLOWED_RESOURCE_ACTIONS: Record<
  FieldActionType,
  TreeResourceChangeIndicator[]
> = {
  classify: [TreeResourceChangeIndicator.ADDITION],
  approve: [],
  "un-approve": [],
  promote: [],
  "promote-removals": [TreeResourceChangeIndicator.REMOVAL],
  mute: [
    TreeResourceChangeIndicator.REMOVAL,
    TreeResourceChangeIndicator.CHANGE,
  ],
  "un-mute": [],
  "assign-categories": [],
};
