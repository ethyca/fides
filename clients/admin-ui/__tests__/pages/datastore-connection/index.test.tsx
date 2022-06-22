import { rest } from "msw";
import { setupServer } from "msw/node";

import {
  BASE_URL,
  CONNECTION_ROUTE,
  DATASTORE_CONNECTION_ROUTE,
  LOGIN_ROUTE,
} from "../../../src/constants";
import DatastoreConnections from "../../../src/pages/datastore-connection";
import { act, render, waitFor } from "../../test-utils";

const useRouter = jest.spyOn(require("next/router"), "useRouter");

afterAll(() => {
  useRouter.mockRestore();
});

describe(`${DATASTORE_CONNECTION_ROUTE}`, () => {
  describe("Auth behavior", () => {
    it("Should redirect to LoginPage when user isn't logged in.", async () => {
      const push = jest.fn();
      useRouter.mockImplementation(() => ({
        push,
      }));

      await act(async () => {
        render(<DatastoreConnections />);
      });

      await waitFor(() => expect(push).toHaveBeenCalledTimes(1));
      expect(push).toHaveBeenCalledWith(LOGIN_ROUTE);
    });

    it(`Should stay on DatastoreConnectionPage when the user is already logged in`, async () => {
      await act(async () => {
        const push = jest.fn();

        useRouter.mockImplementation(() => ({
          pathname: "",
          push,
          prefetch: jest.fn(() => Promise.resolve()),
        }));
        const server = setupServer(
          rest.get(`${BASE_URL}${CONNECTION_ROUTE}`, (req, res) => res())
        );

        server.listen();

        await act(async () => {
          render(<DatastoreConnections />, {
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

        expect(push).toHaveBeenCalledTimes(0);
        server.close();
      });
    });
  });
});
