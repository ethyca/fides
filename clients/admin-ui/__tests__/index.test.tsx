import Home from "../src/pages";
import { mockNextUseRouter, render, screen } from "./test-utils";

// skipping while configWizardFlag exists
describe("Home", () => {
  it.skip("renders the Privacy Requests page by default when logged in", () => {
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

    const message = screen.getAllByText("Privacy Requests")[0];
    expect(message).toBeInTheDocument();
  });
});
