import { AntFlex as Flex, AntFlexProps as FlexProps, Heading } from "fidesui";
import { ReactNode } from "react";

import { NextBreadcrumb, NextBreadcrumbProps } from "./nav/v2/NextBreadcrumb";

interface PageHeaderProps extends Omit<FlexProps, "children"> {
  heading?: ReactNode;
  breadcrumbItems?: NextBreadcrumbProps["items"];
  isSticky?: boolean;
  rightContent?: ReactNode;
  children?: ReactNode;
}

/**
 * A header component for pages.
 *
 * @param heading - The main heading to display in the page header. Can be a string or a React element. String will be rendered as an H1.
 * @param breadcrumbItems - Extends Ant Design Breadcrumb component `items` property. If an item has a `href` property, it will be wrapped in a Next.js link.
 * Can be an array of breadcrumb items (more information on Breadcrumbs component), a React element
 * if you want to render something else, or false to not show any breadcrumbs.
 * @param isSticky - Whether the page header should stick to the top of the page while scrolling. Defaults to true.
 * @param children - Additional content to display in the header below the heading and breadcrumb.
 * @param rightContent - Additional content to display in the header on the right side. Usually for displaying buttons.
 */
const PageHeader = ({
  heading,
  breadcrumbItems,
  isSticky,
  children,
  rightContent,
  style,
  ...props
}: PageHeaderProps): JSX.Element => (
  <Flex
    className="pb-6"
    {...props}
    style={
      isSticky
        ? {
            position: "sticky",
            top: 0,
            left: 0,
            zIndex: 20,
            backgroundColor: "white",
            ...style,
          }
        : style
    }
  >
    <Flex justify="space-between">
      {typeof heading === "string" ? (
        <Heading
          className={!!breadcrumbItems || !!children ? "pb-4" : undefined}
          fontSize="2xl"
        >
          {heading}
        </Heading>
      ) : (
        heading
      )}
      {rightContent && <div>{rightContent}</div>}
    </Flex>

    {!!breadcrumbItems && (
      <NextBreadcrumb
        className={children ? "pb-4" : undefined}
        items={breadcrumbItems}
      />
    )}

    {children}
  </Flex>
);

export default PageHeader;
