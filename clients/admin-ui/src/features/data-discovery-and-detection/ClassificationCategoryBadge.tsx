import { Flex, FlexProps } from "fidesui";

interface TaxonomyBadgeProps extends FlexProps {
  children: React.ReactNode;
}

const TaxonomyBadge = ({ children, onClick, ...props }: TaxonomyBadgeProps) => {
  return (
    <Flex
      fontSize="xs"
      alignItems="center"
      gap={1.5}
      px={1.5}
      h="20px"
      borderWidth="1px"
      borderColor="gray.200"
      borderRadius="sm"
      cursor={onClick ? "pointer" : "default"}
      _hover={onClick ? { bg: "gray.100" } : undefined}
      onClick={onClick}
      {...props}
    >
      {children}
    </Flex>
  );
};

export default TaxonomyBadge;
