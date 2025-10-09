import { AntTypography as Typography } from "fidesui";
import NextLink from "next/link";
import { ComponentProps } from "react";

const { Link: LinkText, Text } = Typography;

export const LinkCell = ({
  href,
  children,
  ...props
}: ComponentProps<typeof LinkText>) => {
  return href ? (
    <NextLink href={href} passHref legacyBehavior>
      <LinkText
        strong
        ellipsis
        onClick={(e) => e.stopPropagation()}
        variant="primary"
        {...props}
      >
        <Text unStyled ellipsis={{ tooltip: children }}>
          {children}
        </Text>
      </LinkText>
    </NextLink>
  ) : (
    <Text strong ellipsis {...props}>
      {children}
    </Text>
  );
};
