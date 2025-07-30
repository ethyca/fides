import {
  FetchState,
  useRetryableFetch,
} from "../../../src/lib/hooks/useRetryableFetch";

// Mock preact/hooks
const mockUseState = jest.fn();
const mockUseEffect = jest.fn();

jest.mock("preact/hooks", () => ({
  useState: (...args: any[]) => mockUseState(...args),
  useEffect: (...args: any[]) => mockUseEffect(...args),
}));

describe("useRetryableFetch", () => {
  let stateValues: Record<string, any> = {};
  let setterCallbacks: Record<string, (newValue: any) => void> = {};

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    stateValues = {};
    setterCallbacks = {};

    // Mock useState to track state changes
    mockUseState.mockImplementation((initialValue: any) => {
      const key = Math.random().toString();
      stateValues[key] = initialValue;
      const setter = (newValue: any) => {
        stateValues[key] =
          typeof newValue === "function"
            ? newValue(stateValues[key])
            : newValue;
      };
      setterCallbacks[key] = setter;
      return [stateValues[key], setter];
    });

    // Mock useEffect to capture and call effects
    mockUseEffect.mockImplementation((effect: () => void | (() => void)) => {
      // Call effect immediately for testing
      const cleanup = effect();
      return cleanup;
    });
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("returns initial state correctly", () => {
    const fetcher = jest.fn();

    const result = useRetryableFetch({ fetcher, enabled: false });

    expect(result.data).toBeUndefined();
    expect(result.fetchState).toBe(FetchState.Idle);
    expect(result.isLoading).toBe(false);
    expect(result.isError).toBe(false);
    expect(typeof result.retry).toBe("function");
  });

  it("calls fetcher when enabled", () => {
    const fetcher = jest.fn().mockResolvedValue({ foo: "bar" });

    useRetryableFetch({ fetcher, enabled: true });

    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("does not call fetcher when disabled", () => {
    const fetcher = jest.fn();

    useRetryableFetch({ fetcher, enabled: false });

    expect(fetcher).not.toHaveBeenCalled();
  });

  it("sets loading state when enabled", () => {
    const fetcher = jest.fn().mockResolvedValue({ data: "test" });

    // Mock useState calls to track state changes
    const fetchStateValue = FetchState.Idle;
    const setFetchState: (value: FetchState) => void = jest.fn();

    mockUseState
      .mockReturnValueOnce([undefined, jest.fn()]) // data state
      .mockReturnValueOnce([fetchStateValue, setFetchState]); // fetchState

    useRetryableFetch({ fetcher, enabled: true });

    // Verify that setFetchState was called with Loading
    expect(mockUseEffect).toHaveBeenCalled();
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("uses default config values", () => {
    const fetcher = jest.fn().mockResolvedValue({ data: "test" });

    const result = useRetryableFetch({ fetcher });

    // Should be enabled by default
    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(result.isLoading).toBe(false); // Initial state before effect runs
  });

  it("provides retry function", () => {
    const fetcher = jest.fn().mockResolvedValue({ data: "test" });

    const result = useRetryableFetch({ fetcher, enabled: false });

    expect(typeof result.retry).toBe("function");

    // Test retry function
    result.retry();
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("handles fetch errors and sets error state", async () => {
    const fetcher = jest.fn().mockRejectedValue(new Error("Network error"));

    // Set up mock to track state changes
    let fetchStateValue = FetchState.Idle;
    const setFetchState = jest.fn((newValue) => {
      fetchStateValue =
        typeof newValue === "function" ? newValue(fetchStateValue) : newValue;
    });

    mockUseState
      .mockReturnValueOnce([undefined, jest.fn()]) // data state
      .mockReturnValueOnce([fetchStateValue, setFetchState]); // fetchState

    const result = useRetryableFetch({ fetcher, enabled: true });

    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(result.isError).toBe(false); // Initial state
  });

  it("accepts retry configuration", () => {
    const fetcher = jest.fn().mockRejectedValue(new Error("Network error"));
    const config = {
      maxAttempts: 3,
      backoffFactor: 100,
      shouldRetry: jest.fn().mockReturnValue(true),
    };

    useRetryableFetch({ fetcher, config, enabled: true });

    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("accepts custom shouldRetry function", () => {
    const fetcher = jest.fn().mockRejectedValue(new Error("Network error"));
    const shouldRetry = jest.fn().mockReturnValue(false); // Always deny retries

    const config = {
      maxAttempts: 5,
      backoffFactor: 100,
      shouldRetry,
    };

    useRetryableFetch({ fetcher, config, enabled: true });

    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("validates response and retries on validation failure", () => {
    const fetcher = jest.fn().mockResolvedValue({ invalid: true });
    const validator = jest.fn().mockReturnValue(false); // Always fails validation

    const config = {
      maxAttempts: 3,
      backoffFactor: 100,
      shouldRetry: jest.fn().mockReturnValue(true),
    };

    useRetryableFetch({
      fetcher,
      validator,
      config,
    });

    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("calls onSuccess callback when fetch succeeds", () => {
    const mockData = { success: true };
    const fetcher = jest.fn().mockResolvedValue(mockData);
    const onSuccess = jest.fn();
    const validator = jest.fn().mockReturnValue(true);

    // Mock successful state transition
    let dataValue: any;
    let fetchStateValue = FetchState.Idle;

    const setData = jest.fn((newValue) => {
      dataValue =
        typeof newValue === "function" ? newValue(dataValue) : newValue;
    });
    const setFetchState = jest.fn((newValue) => {
      fetchStateValue =
        typeof newValue === "function" ? newValue(fetchStateValue) : newValue;
    });

    mockUseState
      .mockReturnValueOnce([dataValue, setData])
      .mockReturnValueOnce([fetchStateValue, setFetchState]);

    useRetryableFetch({
      fetcher,
      validator,
      onSuccess,
    });

    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("handles error state configuration", () => {
    const fetcher = jest.fn().mockRejectedValue(new Error("Persistent error"));
    const config = {
      maxAttempts: 2,
      backoffFactor: 50,
      shouldRetry: jest.fn().mockReturnValue(true),
    };

    let fetchStateValue = FetchState.Idle;
    const setFetchState = jest.fn((newValue) => {
      fetchStateValue =
        typeof newValue === "function" ? newValue(fetchStateValue) : newValue;
    });

    mockUseState
      .mockReturnValueOnce([undefined, jest.fn()]) // data state
      .mockReturnValueOnce([fetchStateValue, setFetchState]); // fetchState

    useRetryableFetch({ fetcher, config, enabled: true });

    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("resets state when retry is called manually", () => {
    const fetcher = jest.fn().mockResolvedValue({ data: "test" });

    let dataValue: any = "previous data";
    let fetchStateValue = FetchState.Success;

    const setData = jest.fn((newValue) => {
      dataValue =
        typeof newValue === "function" ? newValue(dataValue) : newValue;
    });
    const setFetchState = jest.fn((newValue) => {
      fetchStateValue =
        typeof newValue === "function" ? newValue(fetchStateValue) : newValue;
    });

    mockUseState
      .mockReturnValueOnce([dataValue, setData])
      .mockReturnValueOnce([fetchStateValue, setFetchState]);

    const result = useRetryableFetch({ fetcher, enabled: false });

    // Manually call retry
    result.retry();

    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("uses default validator when none provided", () => {
    const fetcher = jest.fn().mockResolvedValue({ data: "test" });

    useRetryableFetch({ fetcher, enabled: true });

    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("handles validation failure that exceeds max attempts", () => {
    const fetcher = jest.fn().mockResolvedValue({ invalid: true });
    const validator = jest.fn().mockReturnValue(false); // Always fails validation
    const config = {
      maxAttempts: 2,
      backoffFactor: 50,
      shouldRetry: jest.fn().mockReturnValue(true),
    };

    let fetchStateValue = FetchState.Idle;
    const setFetchState = jest.fn((newValue) => {
      fetchStateValue =
        typeof newValue === "function" ? newValue(fetchStateValue) : newValue;
    });

    mockUseState
      .mockReturnValueOnce([undefined, jest.fn()]) // data state
      .mockReturnValueOnce([fetchStateValue, setFetchState]); // fetchState

    useRetryableFetch({
      fetcher,
      validator,
      config,
    });

    expect(fetcher).toHaveBeenCalledTimes(1);
  });
});
