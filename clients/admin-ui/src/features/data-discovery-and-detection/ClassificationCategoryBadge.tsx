import { Flex, FlexProps } from "fidesui";
import React from "react";

interface TaxonomyBadgeProps extends FlexProps {
  children: React.ReactNode;
  closeButton?: React.ReactNode;
}

const TaxonomyBadge = ({
  children,
  onClick,
  closeButton,
  ...props
}: TaxonomyBadgeProps) => {
  return (
    <Flex
      fontSize="xs"
      px={1.5}
      h="20px"
      borderWidth="1px"
      borderColor="gray.200"
      borderRadius="sm"
      _hover={onClick ? { bg: "gray.100" } : undefined}
      {...props}
    >
      <Flex
        alignItems="center"
        gap={1.5}
        cursor={onClick ? "pointer" : "default"}
        onClick={onClick}
      >
        {children}
      </Flex>
      {closeButton}
    </Flex>
  );
};

export default TaxonomyBadge;
