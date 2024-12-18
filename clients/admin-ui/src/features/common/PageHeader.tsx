import { AntFlex as Flex, Heading } from "fidesui";
import { ComponentProps, ReactNode } from "react";

import { NextBreadcrumb, NextBreadcrumbProps } from "./nav/v2/NextBreadcrumb";

interface PageHeaderProps extends ComponentProps<"div"> {
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
  isSticky = true,
  children,
  rightContent,
  style,
  ...props
}: PageHeaderProps): JSX.Element => (
  <div
    {...props}
    style={
      isSticky
        ? {
            position: "sticky",
            top: "-24px",
            paddingTop: "24px",
            paddingBottom: "24px",
            paddingLeft: "40px",
            marginLeft: "-40px",
            paddingRight: "40px",
            marginRight: "-40px",
            marginTop: "-24px",
            left: 0,
            zIndex: 20, // needs to be above Table header but below popovers, modals, drawers, etc.
            backgroundColor: "white",
            ...style,
          }
        : {
            paddingBottom: "24px",
            ...style,
          }
    }
  >
    <Flex justify="space-between">
      {typeof heading === "string" ? (
        <Heading
          className={!!breadcrumbItems || !!children ? "pb-4" : undefined}
          fontSize="2xl"
          data-testid="page-heading"
        >
          {heading}
        </Heading>
      ) : (
        heading
      )}
      {rightContent && (
        <div data-testid="page-header-right-content">{rightContent}</div>
      )}
    </Flex>

    {!!breadcrumbItems && (
      <NextBreadcrumb
        className={children ? "pb-4" : undefined}
        items={breadcrumbItems}
        data-testid="page-breadcrumb"
      />
    )}

    {children}
  </div>
);

export default PageHeader;
