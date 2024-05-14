import { Breadcrumb, BreadcrumbItem, BreadcrumbLink } from "@fidesui/react";
import Link from "next/link";

export interface BreadcrumbsProps {
  breadcrumbs: {
    title: string;
    link?: string;
    onClick?: () => void;
    isOpaque?: boolean;
  }[];
}

const Breadcrumbs: React.FC<BreadcrumbsProps> = ({ breadcrumbs }) => (
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
              as={Link}
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
