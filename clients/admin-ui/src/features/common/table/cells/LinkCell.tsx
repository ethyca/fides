import { Flex, FlexProps, Typography } from "fidesui";
import { Url } from "next/dist/shared/lib/router/router";
import { ComponentProps } from "react";

import { RouterLink } from "~/features/common/nav/RouterLink";

const { Link: LinkText, Text } = Typography;

export const LinkCell = ({
  href,
  children,
  containerProps,
  strong = true,
  ...props
}: Omit<ComponentProps<typeof LinkText>, "href"> & {
  href?: Url;
  containerProps?: FlexProps;
}) => {
  return (
    children && (
      <Flex {...containerProps}>
        {href ? (
          <RouterLink
            href={href}
            strong={strong}
            ellipsis
            onClick={(e) => e.stopPropagation()}
            variant="primary"
            {...props}
          >
            <Text unStyled ellipsis={{ tooltip: children }}>
              {children}
            </Text>
          </RouterLink>
        ) : (
          <Text strong={strong} ellipsis {...props}>
            {children}
          </Text>
        )}
      </Flex>
    )
  );
};
