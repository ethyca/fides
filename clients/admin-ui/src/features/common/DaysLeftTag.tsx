import { Tag } from "fidesui";
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

  let backgroundColor = "";

  switch (true) {
    case daysLeft >= 10:
      backgroundColor = "success.500";
      break;

    case daysLeft < 10 && daysLeft > 4:
      backgroundColor = "warn.500";
      break;

    case daysLeft < 5:
      backgroundColor = "error.500";
      break;

    default:
      break;
  }

  const text = includeText ? `${daysLeft} days left` : daysLeft;

  return (
    <Tag
      backgroundColor={backgroundColor}
      color="white"
      fontWeight="medium"
      fontSize="sm"
    >
      {text}
    </Tag>
  );
};

export default DaysLeftTag;
