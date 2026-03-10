export enum NoticeStatus {
  AVAILABLE = "available",
  ENABLED = "enabled",
  INACTIVE = "inactive",
}

export const getNoticeStatus = (
  systemsApplicable: boolean | undefined,
  disabled: boolean,
  dataUses: string[],
) => {
  if (!dataUses) {
    return NoticeStatus.INACTIVE;
  }
  if (systemsApplicable) {
    return disabled ? NoticeStatus.AVAILABLE : NoticeStatus.ENABLED;
  }
  return NoticeStatus.INACTIVE;
};
