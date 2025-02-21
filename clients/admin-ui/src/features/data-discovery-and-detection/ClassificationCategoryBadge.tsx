import { Badge, BadgeProps } from "fidesui";
import { ReactElement } from "react";

interface ClassificationCategoryBadgeProps extends BadgeProps {
  classification?: string | ReactElement;
  children: React.ReactNode;
}

const ClassificationCategoryBadge = ({
  children,
  onClick,
  ...props
}: ClassificationCategoryBadgeProps) => {
  return (
    <Badge
      variant="taxonomy"
      textTransform="none"
      fontWeight="normal"
      display="flex"
      alignItems="center"
      gap={1.5}
      as={onClick ? "button" : undefined}
      onClick={onClick}
      _hover={onClick ? { borderColor: "primary.900" } : undefined}
      {...props}
    >
      {children}
    </Badge>
  );
};

export default ClassificationCategoryBadge;
