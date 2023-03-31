import { Flex, Text } from "@fidesui/react";
import React from "react";
import ResolvedIcon from "./ResolvedIcon";

type CardProps = {
  title: string;
  iconPath: string;
  description: string;
  onClick: () => void;
};

const Card: React.FC<CardProps> = ({
  title,
  iconPath,
  description,
  onClick,
}) => (
  <Flex
    as="button"
    bg="white"
    borderRadius={12}
    boxShadow="base"
    cursor="pointer"
    data-testid="card"
    flexDirection="column"
    gap="12px"
    h="176px"
    key={title}
    m={2}
    onClick={() => {
      onClick();
    }}
    padding="24px"
    textAlign="left"
    transition="box-shadow 50ms"
    userSelect="none"
    w="304px"
    _hover={{
      border: "1px solid",
      borderColor: "complimentary.500",
      boxShadow:
        "0px 10px 15px -3px rgba(0, 0, 0, 0.1), 0px 4px 6px -2px rgba(0, 0, 0, 0.05)",
    }}
    _focus={{
      border: "1px solid",
      borderColor: "complimentary.500",
      boxShadow:
        "0px 10px 15px -3px rgba(0, 0, 0, 0.1), 0px 4px 6px -2px rgba(0, 0, 0, 0.05)",
      outline: "none",
    }}
  >
    <ResolvedIcon iconPath={iconPath} iconBoxSize={"32px"} description={description}/>
    <Text
      color="gray.600"
      fontSize="md"
      fontWeight="semibold"
      lineHeight="24px"
    >
      {title}
    </Text>
    <Text
      color="gray.600"
      fontSize="xs"
      fontWeight="normal"
      lineHeight="16px"
      noOfLines={3}
    >
      {description}
    </Text>
  </Flex>
);

export default Card;
