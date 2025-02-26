import { Flex, Image, Text } from "fidesui";
import React from "react";

type CardProps = {
  title: string;
  iconPath: string;
  description: string;
  onClick: () => void;
};

const Card = ({ title, iconPath, description, onClick }: CardProps) => (
  <Flex
    as="button"
    bg="white"
    borderRadius={12}
    boxShadow="base"
    cursor="pointer"
    data-testid="card"
    flexDirection="column"
    gap="12px"
    minH="176px"
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
    border="1px solid"
    borderColor="transparent"
  >
    <Image alt={description} boxSize="32px" src={iconPath} />
    <Text
      color="gray.800"
      fontSize="md"
      fontWeight="semibold"
      lineHeight="24px"
    >
      {title}
    </Text>
    <Text color="gray.800" fontSize="xs" fontWeight="normal" lineHeight="16px">
      {description}
    </Text>
  </Flex>
);

export default Card;
