import classNames from "classnames";
import { Divider, Flex, Icons, Text, Typography } from "fidesui";
import { ReactNode } from "react";

import styles from "./NeedsAttentionFrame.module.scss";

const { Title } = Typography;

interface NeedsAttentionFrameProps {
  description: string;
  variant?: "error" | "warning";
  rightAction?: ReactNode;
  children: ReactNode;
}

const NeedsAttentionFrame = ({
  description,
  variant = "error",
  rightAction,
  children,
}: NeedsAttentionFrameProps) => {
  const isAlt = variant === "warning";

  return (
    <div role="region" aria-label="Needs attention">
      <Flex align="center" justify="space-between">
        <Flex align="center" gap={12}>
          <Icons.WarningAltFilled
            size={18}
            className={classNames(styles.icon, { [styles.iconAlt]: isAlt })}
          />
          <div>
            <Title level={4} className="!m-0">
              Needs attention
            </Title>
            <Text type="secondary">{description}</Text>
          </div>
        </Flex>
        {rightAction}
      </Flex>
      <Divider className="mb-4" />
      {children}
    </div>
  );
};

export default NeedsAttentionFrame;
