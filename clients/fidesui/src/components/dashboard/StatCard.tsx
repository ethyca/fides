import { Card, CardProps, theme, Typography } from "antd";
import classNames from "classnames";
import React from "react";

const { Text } = Typography;

export interface StatCardProps extends Omit<CardProps, "content" | "title"> {
  title?: string;
  stat: React.ReactNode;
  content?: React.ReactNode;
  footer?: React.ReactNode;
  footerClassName?: string;
}

const StatCard = ({
  title,
  stat,
  content,
  footer,
  footerClassName = "h-16",
  ...rest
}: StatCardProps) => {
  const { token } = theme.useToken();

  const cardBodyPadding = token.Card?.bodyPadding ?? token.paddingLG;

  return (
    <Card variant="borderless" {...rest}>
      {title && <Text type="secondary">{title}</Text>}
      <div className={classNames({ "mt-1": title })}>{stat}</div>
      {content && <div className="mt-3">{content}</div>}
      {footer && (
        <div
          className={classNames("mt-3", footerClassName)}
          style={{
            marginLeft: -cardBodyPadding,
            marginRight: -cardBodyPadding,
            marginBottom: -cardBodyPadding,
          }}
        >
          {footer}
        </div>
      )}
    </Card>
  );
};

export default StatCard;
