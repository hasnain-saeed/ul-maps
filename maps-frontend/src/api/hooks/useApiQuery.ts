import { useQuery, type UseQueryOptions } from '@tanstack/react-query';
import type { QueryResult, ApiError } from '../types/common';

export function useApiQuery<T>(
  queryKey: (string | number)[],
  queryFn: () => Promise<T>,
  options?: Omit<UseQueryOptions<T, ApiError>, 'queryKey' | 'queryFn'>
): QueryResult<T> {
  const { data, isLoading, isError, error } = useQuery({
    queryKey,
    queryFn,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    ...options,
  });

  return {
    data,
    isLoading,
    isError,
    error: error || null,
  };
}