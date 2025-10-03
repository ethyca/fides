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
      <LinkText strong ellipsis onClick={(e) => e.stopPropagation()} {...props}>
        {children}
      </LinkText>
    </NextLink>
  ) : (
    <Text strong ellipsis {...props}>
      {children}
    </Text>
  );
};
