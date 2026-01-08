import type { HeliosData, JanusData, LetheData } from "../types";
import { dummyDashboardData } from "../data/dummyData";

/**
 * Hook for fetching dashboard data
 * TODO: Replace with real API calls when backend is ready
 *
 * @example
 * const { helios, janus, lethe, isLoading } = useDashboardData();
 */
export const useDashboardData = () => {
  // TODO: Replace with actual API calls
  // const { data, isLoading, error } = useGetDashboardDataQuery();
  // return { ...data, isLoading, error };

  // For now, return dummy data
  // This will be replaced with real API calls
  return {
    ...dummyDashboardData,
    isLoading: false,
    error: null,
  };
};

/**
 * Hook for Helios section data
 * TODO: Replace with real API calls
 */
export const useHeliosData = (): {
  data: HeliosData;
  isLoading: boolean;
  error: unknown;
} => {
  // TODO: Replace with actual API call
  // const { data, isLoading, error } = useGetHeliosDataQuery();
  // return { data, isLoading, error };

  // For now, return dummy data
  return {
    data: dummyDashboardData.helios,
    isLoading: false,
    error: null,
  };
};

/**
 * Hook for Janus section data
 * TODO: Replace with real API calls
 */
export const useJanusData = (): {
  data: JanusData;
  isLoading: boolean;
  error: unknown;
} => {
  // TODO: Replace with actual API call
  // const { data, isLoading, error } = useGetJanusDataQuery();
  // return { data, isLoading, error };

  // For now, return dummy data
  return {
    data: dummyDashboardData.janus,
    isLoading: false,
    error: null,
  };
};

/**
 * Hook for Lethe section data
 * TODO: Replace with real API calls
 */
export const useLetheData = (): {
  data: LetheData;
  isLoading: boolean;
  error: unknown;
} => {
  // TODO: Replace with actual API call
  // const { data, isLoading, error } = useGetLetheDataQuery();
  // return { data, isLoading, error };

  // For now, return dummy data
  return {
    data: dummyDashboardData.lethe,
    isLoading: false,
    error: null,
  };
};

