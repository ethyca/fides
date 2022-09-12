import { mockNextUseRouter } from "~/test-utils";

import Home from "../src/pages";
import { render, screen } from "./test-utils";

describe("Home", () => {
  it("renders the Subject Requests page by default when logged in", () => {
    mockNextUseRouter({ route: "/" });
    render(<Home />, {
      preloadedState: {
        auth: {
          user: {
            username: "Test",
          },
          token: "valid-token",
        },
      },
    });

    const message = screen.getAllByText("Subject Requests")[0];
    expect(message).toBeInTheDocument();
  });

  // TODO: Either update or remove this test. We no longer use the SessionProvider from next/auth
  // skip until this is fixed in fidesops
  // it.skip("renders a logged out notification when no session is present", () => {
  //   render(
  //     <SessionProvider>
  //       <Home session={null} />
  //     </SessionProvider>
  //   );
  //
  //   const message = screen.getByText("You are not logged in.");
  //   expect(message).toBeInTheDocument();
  // });
});
