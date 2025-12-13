import { PrivacyNoticeRowType } from "~/features/privacy-notices/table/PrivacyNoticeRowType";

export enum NoticeStatus {
  AVAILABLE = "available",
  ENABLED = "enabled",
  INACTIVE = "inactive",
}

export const getNoticeStatus = (record: PrivacyNoticeRowType) => {
  const {
    systems_applicable: systemsApplicable,
    disabled,
    data_uses: dataUses,
  } = record;
  if (!dataUses) {
    return NoticeStatus.INACTIVE;
  }
  if (systemsApplicable) {
    return disabled ? NoticeStatus.AVAILABLE : NoticeStatus.ENABLED;
  }
  return NoticeStatus.INACTIVE;
};
