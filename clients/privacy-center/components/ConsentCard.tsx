import React from "react";
import Card from "./Card";

type ConsentCardProps = {
  onOpen: () => void;
};

const ConsentCard: React.FC<ConsentCardProps> = ({ onOpen }) => (
  <Card
    title="Manage my consent"
    iconPath="consent.svg"
    description="Manage how we use your data, including the option to select Do Not Sell My Personal Information."
    onClick={onOpen}
  />
);

export default ConsentCard;
