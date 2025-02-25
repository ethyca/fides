import { AntTag as Tag } from "fidesui";
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
    return null;
  }

  let color = "";

  switch (true) {
    case daysLeft >= 10:
      color = "success";
      break;

    case daysLeft < 10 && daysLeft > 4:
      color = "warning";
      break;

    case daysLeft < 5:
      color = "error";
      break;

    default:
      break;
  }

  const text = includeText ? `${daysLeft} days left` : daysLeft;

  return <Tag color={color}>{text}</Tag>;
};

export default DaysLeftTag;
