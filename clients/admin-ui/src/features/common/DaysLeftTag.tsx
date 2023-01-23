import { Tag } from "@fidesui/react";
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
      backgroundColor = "green.500";
      break;

    case daysLeft < 10 && daysLeft > 4:
      backgroundColor = "orange.500";
      break;

    case daysLeft < 5:
      backgroundColor = "red.400";
      break;

    default:
      break;
  }

  const text = includeText ? `${daysLeft} days left` : daysLeft;

  return (
    <Tag backgroundColor={backgroundColor} color="white">
      {text}
    </Tag>
  );
};

export default DaysLeftTag;
