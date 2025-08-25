import { useAuth } from "~/features/auth/authContext";
import {
  useGetProtectedDataQuery,
  useGetProtectedDataByIdQuery,
  useCreateProtectedDataMutation,
  useUpdateProtectedDataMutation,
  useDeleteProtectedDataMutation,
  ProtectedDataRequest,
} from "./protected-data.slice";

/**
 * Custom hooks that automatically include authentication token
 * These hooks wrap the generated RTK Query hooks and inject the auth token
 */

export const useAuthenticatedProtectedData = (params: {
  id?: string;
  page?: number;
  size?: number;
} = {}) => {
  const { token } = useAuth();
  return useGetProtectedDataQuery({ ...params, token });
};

export const useAuthenticatedProtectedDataById = (id: string) => {
  const { token } = useAuth();
  return useGetProtectedDataByIdQuery({ id, token });
};

export const useAuthenticatedCreateProtectedData = () => {
  const { token } = useAuth();
  const [createMutation, result] = useCreateProtectedDataMutation();

  const createProtectedData = (data: ProtectedDataRequest) => {
    if (!token) {
      throw new Error("Authentication token is required");
    }
    return createMutation({ data, token });
  };

  return [createProtectedData, result] as const;
};

export const useAuthenticatedUpdateProtectedData = () => {
  const { token } = useAuth();
  const [updateMutation, result] = useUpdateProtectedDataMutation();

  const updateProtectedData = (id: string, data: Partial<ProtectedDataRequest>) => {
    if (!token) {
      throw new Error("Authentication token is required");
    }
    return updateMutation({ id, data, token });
  };

  return [updateProtectedData, result] as const;
};

export const useAuthenticatedDeleteProtectedData = () => {
  const { token } = useAuth();
  const [deleteMutation, result] = useDeleteProtectedDataMutation();

  const deleteProtectedData = (id: string) => {
    if (!token) {
      throw new Error("Authentication token is required");
    }
    return deleteMutation({ id, token });
  };

  return [deleteProtectedData, result] as const;
};
