import React from "react";
import { Heading, Text, Stack, Box, Image, HStack } from "@fidesui/react";

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
  <Box
    as="button"
    key={title}
    bg="white"
    py={8}
    px={6}
    border="1px solid"
    borderColor="gray.200"
    borderRadius={4}
    boxShadow="base"
    maxWidth={["100%", "100%", "100%", 304]}
    transition="box-shadow 50ms"
    cursor="pointer"
    userSelect="none"
    m={2}
    _hover={{
      boxShadow: "0px 20px 25px -5px rgba(0, 0, 0, 0.1), 0px 10px 10px -5px rgba(0, 0, 0, 0.04)",
    }}
    _focus={{
      outline: "none",
      boxShadow: "0px 20px 25px -5px rgba(0, 0, 0, 0.1), 0px 10px 10px -5px rgba(0, 0, 0, 0.04)",
    }}
    onClick={() => {
      onClick();
    }}
  >
    <Stack spacing={7}>
      <HStack justifyContent="center">
        <Image src={iconPath} alt={description} width="54px" height="54px" />
      </HStack>

      <Stack spacing={1} textAlign="center">
        <Heading
          fontSize="large"
          fontWeight="semibold"
          lineHeight="28px"
          color="gray.600"
        >
          {title}
        </Heading>
        <Text fontSize="xs" color="gray.600">
          {description}
        </Text>
      </Stack>
    </Stack>
  </Box>
);

export default Card;
