import { Button, Typography } from "fidesui";
import NextLink, { LinkProps as NextLinkProps } from "next/link";
import { useRouter } from "next/router";
import {
  Children,
  ComponentProps,
  isValidElement,
  MouseEvent,
  ReactNode,
  useCallback,
  useEffect,
} from "react";
import type { UrlObject } from "url";

const { Link: TypographyLink } = Typography;

type Href = string | UrlObject;

export const formatHref = (url: UrlObject): string => {
  const pathname = url.pathname ?? "";
  let search = "";
  if (url.search) {
    search = url.search.startsWith("?") ? url.search : `?${url.search}`;
  } else if (url.query) {
    const params =
      typeof url.query === "string"
        ? url.query
        : new URLSearchParams(
            Object.entries(url.query).flatMap(([k, v]) => {
              if (v === null || v === undefined) {
                return [];
              }
              return Array.isArray(v)
                ? v.map((item) => [k, String(item)] as [string, string])
                : [[k, String(v)] as [string, string]];
            }),
          ).toString();
    if (params) {
      search = `?${params}`;
    }
  }
  let hash = "";
  if (url.hash) {
    hash = url.hash.startsWith("#") ? url.hash : `#${url.hash}`;
  }
  return `${pathname}${search}${hash}`;
};

type TypographyLinkProps = Omit<
  ComponentProps<typeof TypographyLink>,
  "href" | "onClick"
>;

export interface RouterLinkProps extends TypographyLinkProps {
  href: Href;
  children: ReactNode;
  onClick?: (e: MouseEvent<HTMLElement>) => void;
  replace?: NextLinkProps["replace"];
  scroll?: NextLinkProps["scroll"];
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
  target,
  rel,
  ...typographyProps
}: RouterLinkProps) => {
  const router = useRouter();
  const isButtonChild = isAntButtonChild(children);
  const hrefString = typeof href === "string" ? href : formatHref(href);

  const prefetchHref = useCallback(() => {
    router.prefetch(hrefString).catch(() => {
      // prefetch is best-effort; ignore failures
    });
  }, [router, hrefString]);

  useEffect(() => {
    if (
      isButtonChild ||
      process.env.NODE_ENV !== "production" ||
      prefetch === false ||
      prefetch === null ||
      target === "_blank"
    ) {
      return;
    }
    prefetchHref();
  }, [isButtonChild, prefetch, prefetchHref, target]);

  if (isButtonChild) {
    return (
      <NextLink
        href={href}
        replace={replace}
        scroll={scroll}
        prefetch={prefetch}
        target={target}
        rel={rel}
      >
        {children}
      </NextLink>
    );
  }

  return (
    <TypographyLink
      href={hrefString}
      target={target}
      rel={rel}
      onMouseEnter={prefetch === null ? prefetchHref : undefined}
      onClick={(e) => {
        onClick?.(e);
        if (
          e.defaultPrevented ||
          e.button !== 0 ||
          e.metaKey ||
          e.ctrlKey ||
          e.shiftKey ||
          e.altKey ||
          target === "_blank"
        ) {
          // Let the browser handle new-tab / modified clicks natively.
          return;
        }
        e.preventDefault();
        const navigation = replace
          ? router.replace(href, undefined, { scroll })
          : router.push(href, undefined, { scroll });
        navigation.catch(() => {
          // navigation errors are surfaced by Next's own error handling
        });
      }}
      {...typographyProps}
    >
      {children}
    </TypographyLink>
  );
};
