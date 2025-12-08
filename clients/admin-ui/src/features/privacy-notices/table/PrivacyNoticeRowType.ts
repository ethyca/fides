// we have to alias this because Ant Table automatically sets the "expandable"

import { LimitedPrivacyNoticeResponseSchema } from "~/types/api/models/LimitedPrivacyNoticeResponseSchema";

// prop on table rows if the data type has a "children" property
export interface PrivacyNoticeRowType
  extends Omit<LimitedPrivacyNoticeResponseSchema, "children"> {
  noticeChildren?: LimitedPrivacyNoticeResponseSchema["children"];
}
