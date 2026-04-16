import { fireEvent, render, screen } from "@testing-library/react";
import { Button } from "fidesui";

import { formatHref, RouterLink } from "./RouterLink";

const mockPush = jest.fn().mockResolvedValue(true);
const mockReplace = jest.fn().mockResolvedValue(true);
const mockPrefetch = jest.fn().mockResolvedValue(undefined);

jest.mock("next/router", () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
    prefetch: mockPrefetch,
    pathname: "/",
    query: {},
    asPath: "/",
  }),
}));

describe("formatHref", () => {
  it("returns just the pathname when no query or hash is present", () => {
    expect(formatHref({ pathname: "/policies" })).toBe("/policies");
  });

  it("returns an empty string when given an empty UrlObject", () => {
    expect(formatHref({})).toBe("");
  });

  it("serializes a single query param", () => {
    expect(formatHref({ pathname: "/policies", query: { id: "abc" } })).toBe(
      "/policies?id=abc",
    );
  });

  it("serializes multiple query params", () => {
    expect(
      formatHref({ pathname: "/policies", query: { id: "abc", page: "2" } }),
    ).toBe("/policies?id=abc&page=2");
  });

  it("serializes array query values as repeated keys", () => {
    expect(
      formatHref({ pathname: "/policies", query: { tag: ["a", "b"] } }),
    ).toBe("/policies?tag=a&tag=b");
  });

  it("skips null and undefined query values", () => {
    expect(
      formatHref({
        pathname: "/policies",
        query: {
          id: "abc",
          missing: undefined,
          also: null as unknown as string,
        },
      }),
    ).toBe("/policies?id=abc");
  });

  it("URL-encodes special characters in query values", () => {
    expect(
      formatHref({ pathname: "/policies", query: { name: "hello world&" } }),
    ).toBe("/policies?name=hello+world%26");
  });

  it("appends a hash, prefixing # when missing", () => {
    expect(formatHref({ pathname: "/docs", hash: "section" })).toBe(
      "/docs#section",
    );
    expect(formatHref({ pathname: "/docs", hash: "#section" })).toBe(
      "/docs#section",
    );
  });

  it("uses an explicit search string and ignores query when both are set", () => {
    expect(
      formatHref({
        pathname: "/policies",
        search: "id=abc",
        query: { ignored: "yes" },
      }),
    ).toBe("/policies?id=abc");
  });

  it("preserves a leading ? on search", () => {
    expect(formatHref({ pathname: "/policies", search: "?id=abc" })).toBe(
      "/policies?id=abc",
    );
  });

  it("treats a string query as a pre-encoded query string", () => {
    expect(formatHref({ pathname: "/policies", query: "id=abc&page=2" })).toBe(
      "/policies?id=abc&page=2",
    );
  });

  it("combines pathname, query, and hash", () => {
    expect(
      formatHref({
        pathname: "/policies",
        query: { id: "abc" },
        hash: "details",
      }),
    ).toBe("/policies?id=abc#details");
  });
});

describe("RouterLink", () => {
  beforeEach(() => {
    mockPush.mockClear();
    mockReplace.mockClear();
    mockPrefetch.mockClear();
  });

  describe("with an antd Button child", () => {
    it("wraps the button in a next/link anchor with the given href", () => {
      render(
        <RouterLink href="/dashboard">
          <Button>Go</Button>
        </RouterLink>,
      );

      const anchor = screen.getByRole("link", { name: "Go" });
      expect(anchor).toHaveAttribute("href", "/dashboard");
      expect(anchor.querySelector("button")).not.toBeNull();
    });

    it("forwards target and rel to the next/link anchor", () => {
      render(
        <RouterLink href="/dashboard" target="_blank" rel="noopener noreferrer">
          <Button>External</Button>
        </RouterLink>,
      );

      const anchor = screen.getByRole("link", { name: "External" });
      expect(anchor).toHaveAttribute("target", "_blank");
      expect(anchor).toHaveAttribute("rel", "noopener noreferrer");
    });

    it("does not call router.push on click (next/link handles it)", () => {
      render(
        <RouterLink href="/dashboard">
          <Button>Go</Button>
        </RouterLink>,
      );

      fireEvent.click(screen.getByRole("button", { name: "Go" }));
      expect(mockPush).not.toHaveBeenCalled();
    });
  });

  describe("with non-Button children", () => {
    it("renders a Typography.Link-styled anchor with the resolved href", () => {
      render(<RouterLink href="/details">Details</RouterLink>);

      const anchor = screen.getByRole("link", { name: "Details" });
      expect(anchor).toHaveAttribute("href", "/details");
    });

    it("serializes a UrlObject href for the anchor attribute", () => {
      render(
        <RouterLink href={{ pathname: "/policies", query: { id: "abc" } }}>
          My policy
        </RouterLink>,
      );

      expect(screen.getByRole("link", { name: "My policy" })).toHaveAttribute(
        "href",
        "/policies?id=abc",
      );
    });

    it("calls router.push with the original href on plain left click", () => {
      const href = { pathname: "/policies", query: { id: "abc" } };
      render(<RouterLink href={href}>My policy</RouterLink>);

      fireEvent.click(screen.getByRole("link", { name: "My policy" }), {
        button: 0,
      });
      expect(mockPush).toHaveBeenCalledWith(href, undefined, {
        scroll: undefined,
      });
    });

    it("does not intercept meta/ctrl/shift/alt/middle clicks", () => {
      render(<RouterLink href="/details">Details</RouterLink>);
      const anchor = screen.getByRole("link", { name: "Details" });

      fireEvent.click(anchor, { button: 0, metaKey: true });
      fireEvent.click(anchor, { button: 0, ctrlKey: true });
      fireEvent.click(anchor, { button: 0, shiftKey: true });
      fireEvent.click(anchor, { button: 0, altKey: true });
      fireEvent.click(anchor, { button: 1 });

      expect(mockPush).not.toHaveBeenCalled();
    });

    it("runs a custom onClick before the default handler and respects preventDefault", () => {
      const onClick = jest.fn((e) => e.preventDefault());
      render(
        <RouterLink href="/details" onClick={onClick}>
          Details
        </RouterLink>,
      );

      fireEvent.click(screen.getByRole("link", { name: "Details" }));
      expect(onClick).toHaveBeenCalledTimes(1);
      expect(mockPush).not.toHaveBeenCalled();
    });

    it("does not intercept clicks when target=_blank", () => {
      render(
        <RouterLink href="/details" target="_blank" rel="noopener noreferrer">
          External details
        </RouterLink>,
      );
      const anchor = screen.getByRole("link", { name: "External details" });
      expect(anchor).toHaveAttribute("target", "_blank");
      expect(anchor).toHaveAttribute("rel", "noopener noreferrer");

      fireEvent.click(anchor, { button: 0 });
      expect(mockPush).not.toHaveBeenCalled();
    });

    it("falls through to text mode when a Button is wrapped in a fragment", () => {
      render(
        <RouterLink href="/details">
          {/* eslint-disable-next-line react/jsx-no-useless-fragment */}
          <>
            <Button>Go</Button>
          </>
        </RouterLink>,
      );

      // Text mode uses Typography.Link which renders an <a>; clicking should
      // trigger router.push, proving the component did not take the wrap path.
      fireEvent.click(screen.getByRole("link"));
      expect(mockPush).toHaveBeenCalledWith("/details", undefined, {
        scroll: undefined,
      });
    });

    it("calls router.replace instead of router.push when replace is true", () => {
      render(
        <RouterLink href="/details" replace>
          Details
        </RouterLink>,
      );

      fireEvent.click(screen.getByRole("link", { name: "Details" }));
      expect(mockReplace).toHaveBeenCalledWith("/details", undefined, {
        scroll: undefined,
      });
      expect(mockPush).not.toHaveBeenCalled();
    });

    it("forwards the scroll option to router.push", () => {
      render(
        <RouterLink href="/details" scroll={false}>
          Details
        </RouterLink>,
      );

      fireEvent.click(screen.getByRole("link", { name: "Details" }));
      expect(mockPush).toHaveBeenCalledWith("/details", undefined, {
        scroll: false,
      });
    });

    it("does not prefetch on mount when prefetch is false", () => {
      render(
        <RouterLink href="/details" prefetch={false}>
          Details
        </RouterLink>,
      );
      expect(mockPrefetch).not.toHaveBeenCalled();
    });

    it("does not prefetch on mount when prefetch is null but does on hover", () => {
      render(
        <RouterLink href="/details" prefetch={null}>
          Details
        </RouterLink>,
      );
      expect(mockPrefetch).not.toHaveBeenCalled();

      fireEvent.mouseEnter(screen.getByRole("link", { name: "Details" }));
      expect(mockPrefetch).toHaveBeenCalledWith("/details");
    });

    it("does not prefetch on mount in non-production builds", () => {
      // jest runs with NODE_ENV=test, so default prefetch behaviour is a no-op
      render(<RouterLink href="/details">Details</RouterLink>);
      expect(mockPrefetch).not.toHaveBeenCalled();
    });
  });
});
