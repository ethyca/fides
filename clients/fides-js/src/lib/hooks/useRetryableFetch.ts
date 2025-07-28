import { useEffect, useState } from "preact/hooks";

import {
  TCF_FULL_BACKOFF_FACTOR,
  TCF_FULL_MAX_ATTEMPTS,
} from "../tcf/constants";

export interface RetryConfig {
  maxAttempts?: number;
  backoffFactor?: number;
  shouldRetry?: (attempt: number, result: any, error?: Error) => boolean;
}

export enum FetchState {
  Idle = "idle",
  Loading = "loading",
  Success = "success",
  Error = "error",
}

interface UseRetryableFetchOptions<T> {
  fetcher: () => Promise<T>;
  validator?: (result: T) => boolean;
  onSuccess?: (result: T) => void;
  config?: RetryConfig;
  enabled?: boolean;
}

interface UseRetryableFetchResult<T> {
  data: T | undefined;
  fetchState: FetchState;
  isLoading: boolean;
  isError: boolean;
  retry: () => void;
}

const DEFAULT_CONFIG: Required<RetryConfig> = {
  maxAttempts: TCF_FULL_MAX_ATTEMPTS,
  backoffFactor: TCF_FULL_BACKOFF_FACTOR,
  shouldRetry: () => true,
};

export const useRetryableFetch = <T>({
  fetcher,
  validator = () => true,
  onSuccess,
  config = {},
  enabled = true,
}: UseRetryableFetchOptions<T>): UseRetryableFetchResult<T> => {
  const [data, setData] = useState<T | undefined>(undefined);
  const [fetchState, setFetchState] = useState<FetchState>(FetchState.Idle);

  const finalConfig = { ...DEFAULT_CONFIG, ...config };

  const executeWithRetry = async (attempt = 1): Promise<void> => {
    try {
      const result = await fetcher();

      if (validator(result)) {
        setData(result);
        setFetchState(FetchState.Success);
        onSuccess?.(result);
      } else if (
        attempt < finalConfig.maxAttempts &&
        finalConfig.shouldRetry(attempt, result)
      ) {
        setTimeout(
          () => executeWithRetry(attempt + 1),
          finalConfig.backoffFactor * 2 ** (attempt - 1),
        );
      } else {
        setFetchState(FetchState.Error);
      }
    } catch (err) {
      if (
        attempt < finalConfig.maxAttempts &&
        finalConfig.shouldRetry(attempt, null, err as Error)
      ) {
        setTimeout(
          () => executeWithRetry(attempt + 1),
          finalConfig.backoffFactor * 2 ** (attempt - 1),
        );
      } else {
        setFetchState(FetchState.Error);
      }
    }
  };

  const retry = () => {
    setFetchState(FetchState.Loading);
    setData(undefined);
    executeWithRetry();
  };

  useEffect(() => {
    if (enabled) {
      setFetchState(FetchState.Loading);
      executeWithRetry();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled]);

  return {
    data,
    fetchState,
    isLoading: fetchState === FetchState.Loading,
    isError: fetchState === FetchState.Error,
    retry,
  };
};
