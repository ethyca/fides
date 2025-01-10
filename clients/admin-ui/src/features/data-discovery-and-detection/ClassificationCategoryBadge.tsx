import { Flex, FlexProps } from "fidesui";

interface ClassificationCategoryBadgeProps extends FlexProps {
  classification?: string | JSX.Element;
  children: React.ReactNode;
}

const ClassificationCategoryBadge = ({
  children,
  onClick,
  ...props
}: ClassificationCategoryBadgeProps) => {
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
      as={onClick ? "button" : undefined}
      _hover={onClick ? { bg: "gray.100" } : undefined}
      onClick={onClick}
      {...props}
    >
      {children}
    </Flex>
  );
};

export default ClassificationCategoryBadge;
