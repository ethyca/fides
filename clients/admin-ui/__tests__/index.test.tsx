// __tests__/index.test.tsx
import { render, screen } from "@testing-library/react";
import { SessionProvider } from "next-auth/react";

import Home from "../src/pages/index";

describe("Home", () => {
  // skip until this is fixed in fidesops
  it.skip("renders a logged out notification when no session is present", () => {
    render(
      <SessionProvider>
        <Home session={null} />
      </SessionProvider>
    );

    const message = screen.getByText("You are not logged in.");
    expect(message).toBeInTheDocument();
  });
});
