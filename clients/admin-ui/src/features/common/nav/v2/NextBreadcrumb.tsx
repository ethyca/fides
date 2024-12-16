/* eslint-disable tailwindcss/no-custom-classname */
/* eslint-disable no-param-reassign */
import {
  AntBreadcrumb as Breadcrumb,
  AntBreadcrumbItemType as BreadcrumbItemType,
  AntBreadcrumbProps as BreadcrumbProps,
} from "fidesui";
import { Url } from "next/dist/shared/lib/router/router";
import NextLink from "next/link";
import { ReactNode } from "react";

// Too difficult to make `path` work with Next.js links so we'll just remove it from the type
interface NextBreadcrumbItemType
  extends Omit<BreadcrumbItemType, "path" | "href"> {
  /**
   * becomes NextJS link href
   */
  href?: Url;
  icon?: ReactNode;
}

export interface NextBreadcrumbProps extends Omit<BreadcrumbProps, "items"> {
  items?: NextBreadcrumbItemType[];
}

/**
 * Extends the Ant Design Breadcrumb component to allow for Next.js links. If an item has a `href` property, it will be wrapped in a Next.js link.
 * @returns
 */
export const NextBreadcrumb = ({ items, ...props }: NextBreadcrumbProps) => {
  items?.map((item) => {
    if (item.icon && typeof item.title === "string") {
      item.title = (
        <>
          <span className="anticon align-text-bottom">{item.icon}</span>
          <span>{item.title}</span>
        </>
      );
    }
    if (item.href && item.title) {
      item.title = (
        <NextLink href={item.href} className="ant-breadcrumb-link">
          {item.title}
        </NextLink>
      );
      delete item.href;
    }
    return item;
  });
  const newItems = items as BreadcrumbItemType[];
  return <Breadcrumb items={newItems} {...props} />;
};
