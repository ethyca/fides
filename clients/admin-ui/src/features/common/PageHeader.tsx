import { Box, BoxProps, Flex } from "fidesui";
import { isArray } from "lodash";
import { isValidElement, ReactElement } from "react";

import Breadcrumbs, { BreadcrumbsProps } from "~/features/common/Breadcrumbs";

interface PageHeaderProps extends BoxProps {
  breadcrumbs: BreadcrumbsProps["breadcrumbs"] | ReactElement | false;
  isSticky?: boolean;
  rightContent?: ReactElement;
}

/**
 * A header component for pages.
 *
 * @param breadcrumbs - The breadcrumbs to display in the page header.
 * Can be an array of breadcrumb items (more information on Breadcrumbs component), a React element
 * if you want to render something else, or false to not show any breadcrumbs.
 * @param isSticky - Whether the page header should stick to the top of the page while scrolling. Defaults to true.
 * @param children - Additional content to display in the header at the bottom.
 * @param rightContent - Additional content to display in the header on the right side. Usually for displaying buttons.
 */
const PageHeader = ({
  breadcrumbs,
  isSticky = true,
  children,
  rightContent,
  ...otherProps
}: PageHeaderProps): JSX.Element => (
  <Box
    bgColor="white"
    paddingY={5}
    {...(isSticky ? { position: "sticky", top: 0, left: 0, zIndex: 10 } : {})}
    {...otherProps}
  >
    <Flex alignItems="flex-start">
      <Box flex={1}>
        {/* If breadcrumbs is an array, render the Breadcrumbs component. */}
        {isArray(breadcrumbs) && (
          <Box marginBottom={children ? 4 : 0}>
            <Breadcrumbs breadcrumbs={breadcrumbs} />
          </Box>
        )}
        {/* If breadcrumbs is a React element, render it. */}
        {isValidElement(breadcrumbs) && breadcrumbs}
      </Box>
      {rightContent && <Box>{rightContent}</Box>}
    </Flex>

    {children}
  </Box>
);

export default PageHeader;
