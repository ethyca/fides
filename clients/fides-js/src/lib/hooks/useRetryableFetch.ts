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

interface UseRetryableFetchOptions<T> {
  fetcher: () => Promise<T>;
  validator?: (result: T) => boolean;
  onSuccess?: (result: T) => void;
  config?: RetryConfig;
  enabled?: boolean;
}

interface UseRetryableFetchResult<T> {
  data: T | undefined;
  loading: boolean;
  error: boolean;
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
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  const finalConfig = { ...DEFAULT_CONFIG, ...config };

  const executeWithRetry = async (attempt = 1): Promise<void> => {
    try {
      const result = await fetcher();

      if (validator(result)) {
        setData(result);
        setLoading(false);
        setError(false);
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
        setError(true);
        setLoading(false);
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
        setError(true);
        setLoading(false);
      }
    }
  };

  const retry = () => {
    setLoading(true);
    setError(false);
    setData(undefined);
    executeWithRetry();
  };

  useEffect(() => {
    if (enabled) {
      setLoading(true);
      setError(false);
      executeWithRetry();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled]);

  return {
    data,
    loading,
    error,
    retry,
  };
};
