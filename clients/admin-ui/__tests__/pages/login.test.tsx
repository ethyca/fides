import { rest } from "msw";
import { setupServer } from "msw/node";

import { BASE_API_URN } from "../../src/constants";
import LoginPage from "../../src/pages/login";
import { act, fireEvent, render, screen, waitFor } from "../test-utils";

const useRouter = jest.spyOn(require("next/router"), "useRouter");

afterAll(() => {
  useRouter.mockRestore();
});

describe("/login", () => {
  it("Should redirect when the user logs in successfully", async () => {
    const server = setupServer(
      rest.post(`${BASE_API_URN}/login`, (req, res, ctx) =>
        res(
          ctx.json({
            user_data: {
              username: "Test",
            },
            token_data: {
              access_token: "test-access-token",
            },
          })
        )
      )
    );

    server.listen();

    const push = jest.fn();
    useRouter.mockImplementation(() => ({
      push,
    }));

    await act(async () => {
      render(<LoginPage />);
    });

    expect(push).toBeCalledTimes(0);

    const email = screen.getByRole("textbox", { name: /email/i });
    const passwordInput = screen.getByLabelText(/password/i);
    const loginButton = screen.getByRole("button");

    await act(async () => {
      await fireEvent.change(email, { target: { value: "test-user" } });
      await fireEvent.change(passwordInput, {
        target: { value: "test-user-password" },
      });
      await fireEvent.submit(loginButton);
    });

    await waitFor(() => expect(push).toHaveBeenCalledTimes(1));
    expect(push).toHaveBeenCalledWith("/");

    server.close();
  });

  it('Should redirect to "/" when the user is already logged in', async () => {
    await act(async () => {
      const push = jest.fn();
      useRouter.mockImplementation(() => ({
        push,
      }));

      await act(async () => {
        render(<LoginPage />, {
          preloadedState: {
            auth: {
              user: {
                username: "Test User",
              },
              token: "valid-token",
            },
          },
        });
      });

      expect(push).toHaveBeenCalledWith("/");
      expect(push).toHaveBeenCalledTimes(1);
    });
  });
});
