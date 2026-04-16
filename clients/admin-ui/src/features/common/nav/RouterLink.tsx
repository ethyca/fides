import { Button, Typography } from "fidesui";
import NextLink, { LinkProps as NextLinkProps } from "next/link";
import { useRouter } from "next/router";
import {
  AnchorHTMLAttributes,
  Children,
  ComponentProps,
  isValidElement,
  MouseEvent,
  ReactNode,
  useCallback,
  useEffect,
} from "react";
import type { UrlObject } from "url";

type AnchorProps = Omit<
  AnchorHTMLAttributes<HTMLAnchorElement>,
  "href" | "onClick"
>;

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

interface BaseRouterLinkProps {
  href: Href;
  children: ReactNode;
  onClick?: (e: MouseEvent<HTMLElement>) => void;
  replace?: NextLinkProps["replace"];
  scroll?: NextLinkProps["scroll"];
  prefetch?: NextLinkProps["prefetch"];
  className?: string;
}

export type RouterLinkProps =
  | (BaseRouterLinkProps & { unstyled: true } & AnchorProps)
  | (BaseRouterLinkProps & { unstyled?: false } & TypographyLinkProps);

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
 * Three rendering modes:
 *
 * 1. **Button child** - When the single child is an antd `Button`, wraps it
 *    in `next/link` so Next renders its own `<a>` around the button.
 *    Preserves client-side routing, prefetch, and modifier-click handling.
 *
 * 2. **Unstyled** (`unstyled` prop) - Delegates to `next/link` directly,
 *    rendering a plain `<a>` with no Typography.Link styling. Use this
 *    when wrapping cards, list items, or other non-text content that
 *    shouldn't inherit link colors/underlines. All standard anchor
 *    attributes (className, id, role, aria-*, data-*) are forwarded.
 *
 * 3. **Text mode** (default) - Renders a `Typography.Link`-styled anchor
 *    that intercepts plain left-clicks and uses `router.push` for
 *    client-side navigation. Modifier, middle, and right clicks fall
 *    through to the browser so new-tab / copy-link behaviour continues
 *    to work.
 *
 * Button detection is structural (only a single antd `Button` element is
 * detected). If you need to wrap a custom button-like component, use
 * `unstyled` instead.
 */
export const RouterLink = (props: RouterLinkProps) => {
  const {
    href,
    children,
    onClick,
    replace,
    scroll,
    prefetch,
    unstyled,
    className,
    ...rest
  } = props;

  const router = useRouter();
  const isButtonChild = isAntButtonChild(children);
  const useNextLink = isButtonChild || unstyled;
  const hrefString = typeof href === "string" ? href : formatHref(href);
  const { target } = rest;
  const { rel } = rest;

  // Text-mode prefetch (hooks must be called unconditionally)
  const prefetchHref = useCallback(() => {
    router.prefetch(hrefString).catch(() => {
      // prefetch is best-effort; ignore failures
    });
  }, [router, hrefString]);

  useEffect(() => {
    if (
      useNextLink ||
      process.env.NODE_ENV !== "production" ||
      prefetch === false ||
      prefetch === null ||
      target === "_blank"
    ) {
      return;
    }
    prefetchHref();
  }, [useNextLink, prefetch, prefetchHref, target]);

  // Modes 1 & 2: delegate to NextLink (button child or unstyled)
  if (useNextLink) {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars -- destructure to exclude from spread
    const {
      target: anchorTarget,
      rel: anchorRel,
      ...anchorProps
    } = rest as AnchorProps;
    return (
      <NextLink
        href={href}
        replace={replace}
        scroll={scroll}
        prefetch={prefetch}
        target={target}
        rel={rel}
        className={className}
        onClick={onClick as NextLinkProps["onClick"]}
        {...anchorProps}
      >
        {children}
      </NextLink>
    );
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars -- destructure to exclude from spread
  const {
    target: typTarget,
    rel: typRel,
    ...typographyProps
  } = rest as TypographyLinkProps;
  return (
    <TypographyLink
      href={hrefString}
      target={target}
      rel={rel}
      className={className}
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
