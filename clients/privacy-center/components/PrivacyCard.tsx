import React from "react";

import Card from "./Card";

type PrivacyCardProps = {
  title: string;
  iconPath: string;
  description: string;
  onClick: () => void;
};

const PrivacyCard = ({
  title,
  iconPath,
  description,
  onClick,
}: PrivacyCardProps) => (
  <Card
    title={title}
    iconPath={iconPath}
    description={description}
    onClick={onClick}
  />
);

export default PrivacyCard;
