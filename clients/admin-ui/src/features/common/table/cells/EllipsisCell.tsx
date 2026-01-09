import { Typography } from "fidesui";

interface EllipsisCellProps
  extends React.ComponentProps<typeof Typography.Text> {
  children: React.ReactNode;
}

export const EllipsisCell = ({ children, ...props }: EllipsisCellProps) => {
  return children && typeof children === "string" ? (
    <Typography.Text ellipsis={{ tooltip: children }} {...props}>
      {children}
    </Typography.Text>
  ) : null;
};
