import { Box, BoxProps } from "fidesui";
import { isArray } from "lodash";
import { isValidElement, ReactElement } from "react";

import Breadcrumbs, { BreadcrumbsProps } from "~/features/common/Breadcrumbs";

interface PageHeaderProps extends BoxProps {
  breadcrumbs: BreadcrumbsProps["breadcrumbs"] | ReactElement | false;
  isSticky?: boolean;
}

/**
 * A header component for pages.
 *
 * @param breadcrumbs - The breadcrumbs to display in the page header.
 * Can be an array of breadcrumb items (more information on Breadcrumbs component), a React element
 * if you want to render something else, or false to not show any breadcrumbs.
 * @param isSticky - Whether the page header should stick to the top of the page while scrolling. Defaults to true.
 * @param children - Additional content to display in the header.
 */
const PageHeader = ({
  breadcrumbs,
  isSticky = true,
  children,
  ...otherProps
}: PageHeaderProps): JSX.Element => (
  <Box
    bgColor="white"
    paddingY={5}
    {...(isSticky ? { position: "sticky", top: 0, left: 0, zIndex: 10 } : {})}
    {...otherProps}
  >
    {/* If breadcrumbs is an array, render the Breadcrumbs component. */}
    {isArray(breadcrumbs) && (
      <Box marginBottom={children ? 4 : 0}>
        <Breadcrumbs breadcrumbs={breadcrumbs} />
      </Box>
    )}
    {/* If breadcrumbs is a React element, render it. */}
    {isValidElement(breadcrumbs) && breadcrumbs}

    {children}
  </Box>
);

export default PageHeader;
