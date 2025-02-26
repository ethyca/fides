import {
  Box,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbProps as ChakraBreadcrumbProps,
  HTMLChakraProps,
} from "fidesui";
import { Url } from "next/dist/shared/lib/router/router";
import NextLink from "next/link";

export interface BreadcrumbsProps extends ChakraBreadcrumbProps {
  breadcrumbs: {
    title: string;
    link?: Url; // Next.js link url. It can be a string or an URL object (accepts query params)
    onClick?: () => void;
    icon?: React.ReactNode;
  }[];
  fontSize?: string;
  fontWeight?: string;
  separator?: string;
  lastItemStyles?: HTMLChakraProps<"li">;
  normalItemStyles?: HTMLChakraProps<"li">;
}

/**
 * Breadcrumbs component that shows the path to the current page with links to the previous pages.
 * By default, the last breadcrumb is black, and the rest are gray.
 * @param breadcrumbs - array of breadcrumbs
 * @param breadcrumbs.title - title of the breadcrumb
 * @param breadcrumbs.link - (optional) link to the page
 * @param breadcrumbs.icon - (optional) icon to show before the title
 */
const Breadcrumbs = ({
  breadcrumbs,
  fontSize = "2xl",
  fontWeight = "semibold",
  separator = "->",
  lastItemStyles = {
    color: "black",
  },
  normalItemStyles = {
    color: "gray.500",
  },
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

      if (!breadcumbItem.title) {
        return null;
      }

      return (
        <BreadcrumbItem
          {...normalItemStyles}
          {...(isLast ? lastItemStyles : {})}
          key={breadcumbItem.title}
        >
          {breadcumbItem?.icon && <Box mr={2}>{breadcumbItem.icon}</Box>}
          {breadcumbItem.link ? (
            <BreadcrumbLink
              as={NextLink}
              // @ts-ignore - href for chakra expects string, but can also pass a URL Object because we're using as={NextLink}.
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
