import { useState, useCallback, useRef } from 'react';
import { message } from 'antd';

interface UseApiCallOptions<T = any> {
  successMessage?: string;
  errorMessage?: string;
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
  showMessage?: boolean;
}

interface FailedRequest {
  args: any[];
  timestamp: number;
}

/**
 * 统一的 API 调用 Hook
 * 处理加载状态、错误处理、消息提示和重试
 */
export function useApiCall<T = any, P extends any[] = any[]>(
  apiFunction: (...args: P) => Promise<T>,
  options: UseApiCallOptions<T> = {}
) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [data, setData] = useState<T | null>(null);
  const [canRetryState, setCanRetryState] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);
  const failedRequestRef = useRef<FailedRequest | null>(null);

  const execute = useCallback(
    async (...args: P): Promise<T | null> => {
      // 如果已有请求在进行，先取消
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      abortControllerRef.current = new AbortController();
      setLoading(true);
      setError(null);

      try {
        const result = await apiFunction(...args);
        setData(result);
        failedRequestRef.current = null; // Clear failed request on success
        setCanRetryState(false);

        if (options.showMessage !== false && options.successMessage) {
          message.success(options.successMessage);
        }

        options.onSuccess?.(result);
        return result;
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);

        // Store failed request for retry
        failedRequestRef.current = {
          args,
          timestamp: Date.now(),
        };
        setCanRetryState(true);

        if (options.showMessage !== false && error.message !== 'aborted') {
          const errorMsg = options.errorMessage || error.message || 'API 调用失败';
          message.error(errorMsg);
        }

        options.onError?.(error);
        throw error;
      } finally {
        setLoading(false);
        abortControllerRef.current = null;
      }
    },
    [apiFunction, options]
  );

  // Retry the last failed request
  const retry = useCallback(async (): Promise<T | null> => {
    if (!failedRequestRef.current) {
      message.warning('没有失败的请求可以重试');
      return null;
    }

    return execute(...(failedRequestRef.current.args as P));
  }, [execute]);

  // 清理函数
  const cleanup = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  return {
    execute,
    retry,
    loading,
    error,
    data,
    cleanup,
    isError: error !== null,
    canRetry: canRetryState,
  };
}

/**
 * 简化版 Hook - 仅用于简单的单次 API 调用
 */
export function useAsyncApiCall<T = any, P extends any[] = any[]>(
  apiFunction: (...args: P) => Promise<T>,
  _dependencies: any[] = []
) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [data, setData] = useState<T | null>(null);
  const [canRetryState, setCanRetryState] = useState(false);
  const failedRequestRef = useRef<FailedRequest | null>(null);

  const execute = useCallback(
    async (...args: P) => {
      setLoading(true);
      setError(null);
      try {
        const result = await apiFunction(...args);
        setData(result);
        failedRequestRef.current = null;
        setCanRetryState(false);
        return result;
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);

        failedRequestRef.current = {
          args,
          timestamp: Date.now(),
        };
        setCanRetryState(true);

        message.error(error.message || 'API 调用失败');
        throw error;
      } finally {
        setLoading(false);
      }
    },
    [apiFunction]
  );

  const retry = useCallback(async (): Promise<T | null> => {
    if (!failedRequestRef.current) {
      message.warning('没有失败的请求可以重试');
      return null;
    }

    return execute(...(failedRequestRef.current.args as P));
  }, [execute]);

  return { execute, retry, loading, error, data, canRetry: canRetryState };
}

