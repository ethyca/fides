import { makeStore } from "../../../app/store";
import { STORED_CREDENTIALS_KEY } from "../../../constants";
import { login, logout } from "../auth.slice";

describe("Auth", () => {
  it("should persist auth state to localStorage on login", () => {
    jest.spyOn(Object.getPrototypeOf(window.localStorage), "setItem");
    const store = makeStore();

    store.dispatch(
      login({
        user_data: {
          username: "Test",
        },
        token_data: {
          access_token: "test-access-token",
        },
      })
    );

    expect(window.localStorage.setItem).toHaveBeenCalledWith(
      STORED_CREDENTIALS_KEY,
      JSON.stringify({
        token: "test-access-token",
        user: {
          username: "Test",
        },
      })
    );
  });

  it("should remove auth state from localStorage on logout", () => {
    jest.spyOn(Object.getPrototypeOf(window.localStorage), "removeItem");
    const store = makeStore();

    store.dispatch(logout());

    expect(window.localStorage.removeItem).toHaveBeenCalledWith(
      STORED_CREDENTIALS_KEY
    );
  });
});
