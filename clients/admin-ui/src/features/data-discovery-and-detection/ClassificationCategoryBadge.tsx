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
      borderWidth="1px"
      borderColor="gray.200"
      borderRadius="sm"
      cursor={onClick ? "pointer" : "default"}
      _hover={onClick ? { bg: "gray.50" } : undefined}
      {...props}
    >
      {children}
    </Flex>
  );
};

export default ClassificationCategoryBadge;
