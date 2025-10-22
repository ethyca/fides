import { AntTag as Tag, CUSTOM_TAG_COLOR } from "fidesui";
import React from "react";

import { PrivacyRequestStatus } from "~/types/api/models/PrivacyRequestStatus";

type DaysLeftTagProps = {
  daysLeft?: number;
  includeText: boolean;
  status: PrivacyRequestStatus;
};

const DaysLeftTag = ({ daysLeft, includeText, status }: DaysLeftTagProps) => {
  if (
    !daysLeft ||
    status === PrivacyRequestStatus.COMPLETE ||
    status === PrivacyRequestStatus.CANCELED ||
    status === PrivacyRequestStatus.DENIED ||
    status === PrivacyRequestStatus.IDENTITY_UNVERIFIED
  ) {
    return <span>-</span>;
  }

  let color: CUSTOM_TAG_COLOR | undefined;

  switch (true) {
    case daysLeft >= 10:
      color = CUSTOM_TAG_COLOR.SUCCESS;
      break;

    case daysLeft < 10 && daysLeft > 4:
      color = CUSTOM_TAG_COLOR.WARNING;
      break;

    case daysLeft < 5:
      color = CUSTOM_TAG_COLOR.ERROR;
      break;

    default:
      break;
  }

  const text = includeText ? `${daysLeft} days left` : daysLeft;

  return <Tag color={color}>{text}</Tag>;
};

export default DaysLeftTag;
