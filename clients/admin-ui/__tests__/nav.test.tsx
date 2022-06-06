import { render } from "@testing-library/react";
import { SessionProvider } from "next-auth/react";

import NavBar from "~/features/common/NavBar";
import { mockNextUseRouter } from "~/test-utils";

describe("Home", () => {
  it("renders a navigation bar", () => {
    mockNextUseRouter({ route: "/" });
    const { getByTestId } = render(
      <SessionProvider>
        <NavBar />
      </SessionProvider>
    );
    expect(getByTestId("nav-link-Systems")).toBeInTheDocument();
    expect(getByTestId("nav-link-Datasets")).toBeInTheDocument();
    expect(getByTestId("nav-link-Policies")).toBeInTheDocument();
    expect(getByTestId("nav-link-Taxonomy")).toBeInTheDocument();
    expect(getByTestId("nav-link-User Management")).toBeInTheDocument();
    expect(getByTestId("nav-link-More")).toBeInTheDocument();
  });

  it("renders a nav link as active if at the proper route", () => {
    mockNextUseRouter({ route: "/datasets", pathname: "/datasets" });
    const { getByTestId } = render(
      <SessionProvider>
        <NavBar />
      </SessionProvider>
    );
    expect(getByTestId("nav-link-Systems")).not.toHaveAttribute("data-active");
    expect(getByTestId("nav-link-Datasets")).toHaveAttribute("data-active");
  });
});
