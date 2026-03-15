import { useState, useCallback, useRef } from 'react';
import { message } from 'antd';

interface UseApiCallOptions<T = any> {
  successMessage?: string;
  errorMessage?: string;
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
  showMessage?: boolean;
}

/**
 * 统一的 API 调用 Hook
 * 处理加载状态、错误处理、消息提示
 */
export function useApiCall<T = any, P extends any[] = any[]>(
  apiFunction: (...args: P) => Promise<T>,
  options: UseApiCallOptions<T> = {}
) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [data, setData] = useState<T | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

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

        if (options.showMessage !== false && options.successMessage) {
          message.success(options.successMessage);
        }

        options.onSuccess?.(result);
        return result;
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);

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

  // 清理函数
  const cleanup = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  return {
    execute,
    loading,
    error,
    data,
    cleanup,
    isError: error !== null,
  };
}

/**
 * 简化版 Hook - 仅用于简单的单次 API 调用
 */
export function useAsyncApiCall<T = any, P extends any[] = any[]>(
  apiFunction: (...args: P) => Promise<T>,
  dependencies: any[] = []
) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [data, setData] = useState<T | null>(null);

  const execute = useCallback(
    async (...args: P) => {
      setLoading(true);
      setError(null);
      try {
        const result = await apiFunction(...args);
        setData(result);
        return result;
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
        message.error(error.message || 'API 调用失败');
        throw error;
      } finally {
        setLoading(false);
      }
    },
    [apiFunction]
  );

  return { execute, loading, error, data };
}
