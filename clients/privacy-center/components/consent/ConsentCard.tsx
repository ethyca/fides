import React from "react";

import Card from "~/components/Card";

type ConsentCardProps = {
  title: string;
  iconPath: string;
  description: string;
  onOpen: () => void;
};

const ConsentCard = ({
  title,
  iconPath,
  description,
  onOpen,
}: ConsentCardProps) => (
  <Card
    title={title}
    iconPath={iconPath}
    description={description}
    onClick={onOpen}
  />
);

export default ConsentCard;
