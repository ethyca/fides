import { Card, type CardProps } from "fidesui";
import type { ReactNode } from "react";

const SettingsBox = ({
  title,
  children,
  ...props
}: { title: string; children: ReactNode } & CardProps) => (
  <Card title={title} data-testid={`setting-${title}`} {...props}>
    {children}
  </Card>
);

export default SettingsBox;
