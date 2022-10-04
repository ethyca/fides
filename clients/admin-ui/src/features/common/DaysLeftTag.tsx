import { Tag } from "@fidesui/react";
import React from "react";

type DaysLeftTagProps = {
  daysLeft?: number;
  includeText: boolean;
};

const DaysLeftTag = ({ daysLeft, includeText }: DaysLeftTagProps) => {
  if (!daysLeft) {
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
