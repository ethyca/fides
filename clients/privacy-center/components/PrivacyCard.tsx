import React from "react";

import Card from "./Card";

type PrivacyCardProps = {
  title: string;
  policyKey: string;
  iconPath: string;
  description: string;
  onOpen: (policyKey: string) => void;
};

const PrivacyCard = ({
  title,
  policyKey,
  iconPath,
  description,
  onOpen,
}: PrivacyCardProps) => (
  <Card
    title={title}
    iconPath={iconPath}
    description={description}
    onClick={() => {
      onOpen(policyKey);
    }}
  />
);

export default PrivacyCard;
