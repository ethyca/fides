import {
  Box,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbProps as ChakraBreadcrumbProps,
} from "fidesui";
import { Url } from "next/dist/shared/lib/router/router";
import NextLink from "next/link";

export interface BreadcrumbsProps extends ChakraBreadcrumbProps {
  breadcrumbs: {
    title: string;
    link?: Url; // Next.js link url. It can be a string or an URL object (accepts query params)
    onClick?: () => void;
    isOpaque?: boolean;
    icon?: React.ReactNode;
  }[];
  fontSize?: string;
  fontWeight?: string;
  separator?: string;
}

/**
 * Breadcrumbs component that shows the path to the current page with links to the previous pages.
 * By default, the last breadcrumb is black, and the rest are gray.
 * @param breadcrumbs - array of breadcrumbs
 * @param breadcrumbs.title - title of the breadcrumb
 * @param breadcrumbs.link - (optional) link to the page
 * @param breadcrumbs.icon - (optional) icon to show before the title
 * @param breadcrumbs.onClick - (optional) function to call when the breadcrumb is clicked
 * @param breadcrumbs.isOpaque - (optional) if true, the breadcrumb will be black, otherwise gray
 */
const Breadcrumbs = ({
  breadcrumbs,
  fontSize = "2xl",
  fontWeight = "semibold",
  separator = "->",
  ...otherChakraBreadcrumbProps
}: BreadcrumbsProps) => (
  <Breadcrumb
    separator={separator}
    fontSize={fontSize}
    fontWeight={fontWeight}
    data-testid="breadcrumbs"
    {...otherChakraBreadcrumbProps}
  >
    {breadcrumbs.map((breadcumbItem, index) => {
      const isLast = index + 1 === breadcrumbs.length;
      const hasLink = !!breadcumbItem.link || !!breadcumbItem.onClick;
      return (
        <BreadcrumbItem
          color={isLast || breadcumbItem.isOpaque ? "black" : "gray.500"}
          key={breadcumbItem.title}
        >
          {breadcumbItem?.icon && <Box mr={2}>{breadcumbItem.icon}</Box>}
          {hasLink ? (
            <BreadcrumbLink
              as={NextLink}
              href={breadcumbItem.link}
              isCurrentPage={isLast}
            >
              {breadcumbItem.title}
            </BreadcrumbLink>
          ) : (
            <BreadcrumbLink
              _hover={{ textDecoration: "none", cursor: "default" }}
              isCurrentPage={isLast}
            >
              {breadcumbItem.title}
            </BreadcrumbLink>
          )}
        </BreadcrumbItem>
      );
    })}
  </Breadcrumb>
);
export default Breadcrumbs;
