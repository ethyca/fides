import { Flex, FlexProps, Typography } from "fidesui";
import { ComponentProps, MouseEventHandler } from "react";

const { Link: LinkText, Text } = Typography;

export const InteractiveTextCell = ({
  onClick,
  children,
  containerProps,
  strong = true,
  ...props
}: Omit<ComponentProps<typeof LinkText>, "href"> & {
  onClick: MouseEventHandler<HTMLElement>;
  containerProps?: FlexProps;
}) => {
  return (
    children && (
      <Flex {...containerProps}>
        <LinkText
          role="button"
          strong={strong}
          onClick={(e) => {
            e.stopPropagation();
            onClick(e);
          }}
          variant="primary"
          data-testid="interactive-text-cell"
          {...props}
        >
          <Text unStyled ellipsis={{ tooltip: children }}>
            {children}
          </Text>
        </LinkText>
      </Flex>
    )
  );
};
