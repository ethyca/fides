import { Breadcrumb, Typography } from "fidesui";
import React from "react";

import styles from "../SidePanel.module.scss";

const { Title, Text } = Typography;

interface IdentityProps {
  title: string;
  breadcrumbItems?: Array<{ title: string; href?: string }>;
  description?: string;
}

const Identity: React.FC<IdentityProps> & { slotOrder: number } = ({
  title,
  breadcrumbItems,
  description,
}) => (
  <div className={styles.identity}>
    {breadcrumbItems && (
      <Breadcrumb
        items={breadcrumbItems.map((item) => ({
          title: item.href ? <a href={item.href}>{item.title}</a> : item.title,
        }))}
      />
    )}
    <Title level={4} className={styles.identityTitle}>
      {title}
    </Title>
    {description && <Text type="secondary">{description}</Text>}
  </div>
);
Identity.slotOrder = 0;

export default Identity;
