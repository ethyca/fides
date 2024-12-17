/* eslint-disable tailwindcss/no-custom-classname */
/* eslint-disable no-param-reassign */
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
        if (typeof item.title === "string") {
          // for everything except the current page, truncate the title if it's too long
          item.title = (
            <Text
              style={{
                color: "inherit",
                maxWidth: !isCurrentPage ? 400 : undefined,
              }}
              ellipsis={!isCurrentPage}
            >
              {item.title}
            </Text>
          );
        }
        if (item.icon) {
          item.title = (
            <>
              <span className="anticon align-text-bottom">{item.icon}</span>
              {item.title}
            </>
          );
        }
        if (item.href && item.title) {
          // repeat the ant breadcrumb link class to match the style and margin of the ant breadcrumb item
          item.title = (
            <NextLink href={item.href} className="ant-breadcrumb-link">
              {item.title}
            </NextLink>
          );
          delete item.href;
        }
        return item;
      }),
    [items],
  );
  return (
    <Breadcrumb items={formattedItems as BreadcrumbItemType[]} {...props} />
  );
};
