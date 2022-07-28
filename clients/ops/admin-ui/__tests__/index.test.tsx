// __tests__/index.test.tsx
import Home from "../src/pages/index";
import { render, screen } from "./test-utils";

describe("Home", () => {
  it("renders the Subject Requests page by default when logged in", () => {
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
});
