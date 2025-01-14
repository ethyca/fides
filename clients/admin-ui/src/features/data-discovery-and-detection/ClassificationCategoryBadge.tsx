import { Badge, BadgeProps } from "fidesui";

interface ClassificationCategoryBadgeProps extends BadgeProps {
  classification?: string | JSX.Element;
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
      cursor={onClick ? "pointer" : "default"}
      onClick={onClick}
      _hover={onClick ? { borderColor: "primary.900" } : undefined}
      {...props}
    >
      {children}
    </Badge>
  );
};

export default ClassificationCategoryBadge;
