import React from "react";

import Card from "./Card";

type PrivacyCardProps = {
  title: string;
  iconPath: string;
  description: string;
  onOpen: (index: number) => void;
  index: number;
};

const PrivacyCard = ({
  title,
  iconPath,
  description,
  onOpen,
  index,
}: PrivacyCardProps) => (
  <Card
    title={title}
    iconPath={iconPath}
    description={description}
    onClick={() => {
      onOpen(index);
    }}
  />
);

export default PrivacyCard;
