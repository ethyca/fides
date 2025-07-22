import { AntTypography as Typography } from "fidesui";
import NextLink from "next/link";
import { ComponentProps } from "react";

const { Link, Text } = Typography;

export const LinkCell = ({
  href,
  children,
  ...props
}: ComponentProps<typeof Link>) => {
  return href ? (
    <NextLink href={href} passHref legacyBehavior>
      {/* eslint-disable-next-line jsx-a11y/anchor-is-valid */}
      <Link strong ellipsis onClick={(e) => e.stopPropagation()} {...props}>
        {children}
      </Link>
    </NextLink>
  ) : (
    <Text strong ellipsis {...props}>
      {children}
    </Text>
  );
};
