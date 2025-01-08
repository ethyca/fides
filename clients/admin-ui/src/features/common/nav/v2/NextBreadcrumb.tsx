/* eslint-disable tailwindcss/no-custom-classname */
import {
  AntBreadcrumb as Breadcrumb,
  AntBreadcrumbItemType as BreadcrumbItemType,
  AntBreadcrumbProps as BreadcrumbProps,
  AntTypography as Typography,
} from "fidesui";
import { Url } from "next/dist/shared/lib/router/router";
import NextLink from "next/link";
import { ReactNode, useMemo } from "react";

const { Text } = Typography;

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
 *
 * Note: Since Next.js link is used to wrap the entire item, we cannot do these other customizations as an HOC in FidesUI due to the order of operations. HOC would be applied AFTER the Next.js link is applied, but we want the Next.js link to wrap the entire item after all other customizations. And, of course, we can't use Next.js links in FidesUI.
 */
export const NextBreadcrumb = ({ items, ...props }: NextBreadcrumbProps) => {
  const formattedItems = useMemo(
    () =>
      items?.map((item, i) => {
        const isCurrentPage = i === items.length - 1;
        const modifiedItem = { ...item };
        if (typeof modifiedItem.title === "string") {
          // for everything except the current page, truncate the title if it's too long
          modifiedItem.title = (
            <Text
              style={{
                color: "inherit",
                maxWidth: !isCurrentPage ? 400 : undefined,
              }}
              ellipsis={!isCurrentPage}
            >
              {modifiedItem.title}
            </Text>
          );
        }
        if (modifiedItem.icon) {
          modifiedItem.title = (
            <>
              <span className="anticon align-text-bottom">
                {modifiedItem.icon}
              </span>
              {modifiedItem.title}
            </>
          );
        }
        if (modifiedItem.href && modifiedItem.title) {
          // repeat the ant breadcrumb link class to match the style and margin of the ant breadcrumb item
          modifiedItem.title = (
            <NextLink href={modifiedItem.href} className="ant-breadcrumb-link">
              {modifiedItem.title}
            </NextLink>
          );
          delete modifiedItem.href;
        }
        return modifiedItem;
      }),
    [items],
  );
  return (
    <Breadcrumb items={formattedItems as BreadcrumbItemType[]} {...props} />
  );
};
