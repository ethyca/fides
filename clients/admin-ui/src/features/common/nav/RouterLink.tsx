import { Button, Typography } from "fidesui";
import { formatUrl } from "next/dist/shared/lib/router/utils/format-url";
import NextLink, { LinkProps as NextLinkProps } from "next/link";
import { useRouter } from "next/router";
import {
  Children,
  ComponentProps,
  isValidElement,
  MouseEvent,
  ReactNode,
} from "react";
import type { UrlObject } from "url";

const { Link: TypographyLink } = Typography;

type Href = string | UrlObject;

type TypographyLinkProps = Omit<
  ComponentProps<typeof TypographyLink>,
  "href" | "onClick"
>;

export interface RouterLinkProps extends TypographyLinkProps {
  href: Href;
  children: ReactNode;
  onClick?: (e: MouseEvent<HTMLElement>) => void;
  /** Forwarded to next/link when the child is a Button. */
  replace?: NextLinkProps["replace"];
  /** Forwarded to next/link when the child is a Button. */
  scroll?: NextLinkProps["scroll"];
  /** Forwarded to next/link when the child is a Button. */
  prefetch?: NextLinkProps["prefetch"];
}

const isAntButtonChild = (children: ReactNode): boolean => {
  const arr = Children.toArray(children);
  if (arr.length !== 1) {
    return false;
  }
  const [only] = arr;
  return isValidElement(only) && only.type === Button;
};

/**
 * Shared internal-navigation link for admin-ui.
 *
 * - When the single child is an antd `Button`, wraps it in `next/link` so
 *   Next renders its own `<a>` around the button. Preserves client-side
 *   routing, prefetch, and modifier-click handling.
 * - Otherwise renders a `Typography.Link`-styled anchor that intercepts
 *   plain left-clicks and uses `router.push` for client-side navigation.
 *   Modifier, middle, and right clicks fall through to the browser so
 *   new-tab / copy-link behaviour continues to work.
 *
 * Detection is structural (only a single antd `Button` element is detected).
 * If you need to wrap a custom button-like component, extract its render
 * and wrap the real antd `Button`, or add a `button` escape-hatch prop.
 */
export const RouterLink = ({
  href,
  children,
  onClick,
  replace,
  scroll,
  prefetch,
  ...typographyProps
}: RouterLinkProps) => {
  const router = useRouter();

  if (isAntButtonChild(children)) {
    return (
      <NextLink
        href={href}
        replace={replace}
        scroll={scroll}
        prefetch={prefetch}
      >
        {children}
      </NextLink>
    );
  }

  const hrefString = typeof href === "string" ? href : formatUrl(href);

  return (
    <TypographyLink
      href={hrefString}
      onClick={(e) => {
        onClick?.(e);
        if (
          e.defaultPrevented ||
          e.button !== 0 ||
          e.metaKey ||
          e.ctrlKey ||
          e.shiftKey ||
          e.altKey
        ) {
          // Let the browser handle new-tab / modified clicks natively.
          return;
        }
        e.preventDefault();
        router.push(href);
      }}
      {...typographyProps}
    >
      {children}
    </TypographyLink>
  );
};
