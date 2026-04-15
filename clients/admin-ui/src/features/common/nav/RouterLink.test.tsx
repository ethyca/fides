import { fireEvent, render, screen } from "@testing-library/react";
import { Button } from "fidesui";

import { RouterLink } from "./RouterLink";

const mockPush = jest.fn();

jest.mock("next/router", () => ({
  useRouter: () => ({
    push: mockPush,
    pathname: "/",
    query: {},
    asPath: "/",
  }),
}));

describe("RouterLink", () => {
  beforeEach(() => {
    mockPush.mockClear();
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
      expect(mockPush).toHaveBeenCalledWith(href);
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
      expect(mockPush).toHaveBeenCalledWith("/details");
    });
  });
});
