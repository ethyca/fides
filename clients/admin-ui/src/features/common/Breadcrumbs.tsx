import { Breadcrumb, BreadcrumbItem, BreadcrumbLink } from "fidesui";
import NextLink from "next/link";

export interface BreadcrumbsProps {
  breadcrumbs: {
    title: string;
    link?: string;
    onClick?: () => void;
    isOpaque?: boolean;
  }[];
}

/**
 * Breadcrumbs component that shows the path to the current page with links to the previous pages.
 * By default, the last breadcrumb is black, and the rest are gray.
 * @param breadcrumbs - array of breadcrumbs
 * @param breadcrumbs.title - title of the breadcrumb
 * @param breadcrumbs.link - (optional) link to the page
 * @param breadcrumbs.onClick - (optional) function to call when the breadcrumb is clicked
 * @param breadcrumbs.isOpaque - (optional) if true, the breadcrumb will be black, otherwise gray
 */
const Breadcrumbs = ({ breadcrumbs }: BreadcrumbsProps) => (
  <Breadcrumb
    separator="->"
    fontSize="2xl"
    fontWeight="semibold"
    data-testid="breadcrumbs"
  >
    {breadcrumbs.map((breadcumbItem, index) => {
      const isLast = index + 1 === breadcrumbs.length;
      const hasLink = !!breadcumbItem.link || !!breadcumbItem.onClick;
      return (
        <BreadcrumbItem
          color={isLast || breadcumbItem.isOpaque ? "black" : "gray.500"}
          key={breadcumbItem.title}
        >
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
