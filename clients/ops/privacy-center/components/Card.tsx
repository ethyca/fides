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
    borderRadius={4}
    boxShadow="base"
    maxWidth={["100%", "100%", "100%", 304]}
    transition="box-shadow 50ms"
    cursor="pointer"
    userSelect="none"
    m={2}
    _hover={{
      boxShadow: "complimentary-2xl",
    }}
    _focus={{
      outline: "none",
      boxShadow: "complimentary-2xl",
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
