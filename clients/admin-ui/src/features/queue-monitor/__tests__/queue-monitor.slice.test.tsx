import { configureStore } from "@reduxjs/toolkit";
import { renderHook, waitFor } from "@testing-library/react";
import { rest } from "msw";
import { setupServer } from "msw/node";
import { Provider } from "react-redux";

import { reducer as authReducer } from "~/features/auth/auth.slice";
import { baseApi } from "~/features/common/api.slice";

import { useGetQueueMonitorQuery } from "../queue-monitor.slice";
import { QueueMonitorResponse } from "../types";

// In jest, process.env.NEXT_PUBLIC_FIDESCTL_API is undefined, so
// fetchBaseQuery uses baseUrl="" and requests go to "/queue-monitor" directly.
const API_BASE = "";

// ---------------------------------------------------------------------------
// MSW server
// ---------------------------------------------------------------------------

const server = setupServer();

beforeAll(() => server.listen({ onUnhandledRequest: "warn" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// ---------------------------------------------------------------------------
// Redux test wrapper
// ---------------------------------------------------------------------------

const createTestStore = () =>
  configureStore({
    reducer: {
      [baseApi.reducerPath]: baseApi.reducer,
      auth: authReducer,
    },
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware().concat(baseApi.middleware),
  });

type TestStore = ReturnType<typeof createTestStore>;

const createWrapper = (store: TestStore) => {
  const Wrapper = ({ children }: { children: React.ReactNode }) => (
    <Provider store={store}>{children}</Provider>
  );
  return Wrapper;
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("useGetQueueMonitorQuery", () => {
  it("returns queue data on a successful fetch", async () => {
    const mockResponse: QueueMonitorResponse = {
      sqs_enabled: true,
      queues: [
        {
          queue_name: "fides",
          available: 3,
          delayed: 1,
          in_flight: 0,
        },
        {
          queue_name: "fidesops.messaging",
          available: 0,
          delayed: 0,
          in_flight: 5,
        },
      ],
    };

    server.use(
      rest.get(`${API_BASE}/queue-monitor`, (_req, res, ctx) =>
        res(ctx.status(200), ctx.json(mockResponse)),
      ),
    );

    const store = createTestStore();
    const { result } = renderHook(() => useGetQueueMonitorQuery(), {
      wrapper: createWrapper(store),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockResponse);
    expect(result.current.error).toBeUndefined();
  });

  it("surfaces a 503 response as an error", async () => {
    server.use(
      rest.get(`${API_BASE}/queue-monitor`, (_req, res, ctx) =>
        res(ctx.status(503)),
      ),
    );

    const store = createTestStore();
    const { result } = renderHook(() => useGetQueueMonitorQuery(), {
      wrapper: createWrapper(store),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeDefined();
    expect(result.current.data).toBeUndefined();
  });

  it("surfaces a 403 response as an error", async () => {
    server.use(
      rest.get(`${API_BASE}/queue-monitor`, (_req, res, ctx) =>
        res(ctx.status(403), ctx.json({ detail: "Not Authorized" })),
      ),
    );

    const store = createTestStore();
    const { result } = renderHook(() => useGetQueueMonitorQuery(), {
      wrapper: createWrapper(store),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeDefined();
    expect(result.current.data).toBeUndefined();
  });
});
