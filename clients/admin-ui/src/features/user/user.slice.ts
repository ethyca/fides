import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { HYDRATE } from 'next-redux-wrapper';

import type { AppState } from '../../app/store';
import {
  User,
  UserPasswordUpdate,
  UserPermissionsResponse,
  UserPermissionsUpdate,
  UserResponse,
  UsersListParams,
  UsersResponse,
} from './types';

export interface State {
  id: string;
  page: number;
  size: number;
  user: User;
  token: string | null;
}

const initialState: State = {
  id: '',
  page: 1,
  size: 25,
  user: {
    id: '',
    password: '',
    username: '',
    created_at: '',
  },
  token: null,
};

// Helpers
export const mapFiltersToSearchParams = ({
  page,
  size,
  user,
}: Partial<UsersListParams>) => ({
  ...(page ? { page: `${page}` } : {}),
  ...(typeof size !== 'undefined' ? { size: `${size}` } : {}),
  ...(user ? { username: user.username } : {}),
});

// User API
export const userApi = createApi({
  reducerPath: 'userApi',
  baseQuery: fetchBaseQuery({
    baseUrl: process.env.NEXT_PUBLIC_FIDESOPS_API!,
    prepareHeaders: (headers, { getState }) => {
      const { token } = (getState() as AppState).user;
      headers.set('Access-Control-Allow-Origin', '*');
      if (token) {
        headers.set('authorization', `Bearer ${token}`);
      }
      return headers;
    },
  }),
  tagTypes: ['User'],
  endpoints: (build) => ({
    getAllUsers: build.query<UsersResponse, UsersListParams>({
      query: (filters) => ({
        url: `user`,
        params: mapFiltersToSearchParams(filters),
      }),
      providesTags: () => ['User'],
    }),
    getUserById: build.query<object, string>({
      query: (id) => ({ url: `user/${id}` }),
      providesTags: ['User'],
    }),
    getUserPermissions: build.query<object, string>({
      query: (id) => ({ url: `user/${id}/permission` }),
      providesTags: ['User'],
    }),
    createUser: build.mutation<UserResponse, Partial<User>>({
      query: (user) => ({
        url: 'user',
        method: 'POST',
        body: user,
      }),
      invalidatesTags: ['User'],
    }),
    createUserPermissions: build.mutation<
      UserPermissionsResponse,
      Partial<UserPermissionsResponse>
    >({
      query: (user) => ({
        url: `user/${user?.data?.id}/permission`,
        method: 'POST',
        body: { scopes: user.scope },
      }),
      invalidatesTags: ['User'],
    }),
    editUser: build.mutation<User, Partial<User> & Pick<User, 'id'>>({
      query: ({ id, ...patch }) => ({
        url: `user/${id}`,
        method: 'PUT',
        body: patch,
      }),
      invalidatesTags: ['User'],
      // For optimistic updates
      async onQueryStarted({ id, ...patch }, { dispatch, queryFulfilled }) {
        const patchResult = dispatch(
          // @ts-ignore
          userApi.util.updateQueryData('getUserById', id, (draft) => {
            Object.assign(draft, patch);
          })
        );
        try {
          await queryFulfilled;
        } catch {
          patchResult.undo();
          /**
           * Alternatively, on failure you can invalidate the corresponding cache tags
           * to trigger a re-fetch:
           * dispatch(api.util.invalidateTags(['User']))
           */
        }
      },
    }),
    updateUserPassword: build.mutation<
      UserPasswordUpdate,
      Partial<UserPasswordUpdate> & Pick<UserPasswordUpdate, 'id'>
    >({
      query: ({ id, old_password, new_password }) => ({
        url: `user/${id}/reset-password`,
        method: 'POST',
        body: { old_password, new_password },
      }),
      invalidatesTags: ['User'],
    }),
    updateUserPermissions: build.mutation<
      UserPermissionsUpdate,
      Partial<UserPermissionsUpdate> & Pick<UserPermissionsUpdate, 'id'>
    >({
      query: ({ id, scopes }) => ({
        url: `user/${id}/permission`,
        method: 'PUT',
        body: { id, scopes },
      }),
      invalidatesTags: ['User'],
    }),
    deleteUser: build.mutation<{ success: boolean; id: string }, string>({
      query: (id) => ({
        url: `user/${id}`,
        method: 'DELETE',
      }),
      // Invalidates all queries that subscribe to this User `id` only
      invalidatesTags: ['User'],
    }),
  }),
});

export const {
  useGetAllUsersQuery,
  useGetUserByIdQuery,
  useCreateUserMutation,
  useEditUserMutation,
  useDeleteUserMutation,
  useUpdateUserPasswordMutation,
  useUpdateUserPermissionsMutation,
  useCreateUserPermissionsMutation,
  useGetUserPermissionsQuery,
} = userApi;

export const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: {
    assignToken: (state, action: PayloadAction<string>) => ({
      ...state,
      token: action.payload,
    }),
    setUser: (state, action: PayloadAction<User>) => ({
      ...state,
      page: initialState.page,
      user: action.payload,
    }),
    setPage: (state, action: PayloadAction<number>) => ({
      ...state,
      page: action.payload,
    }),
    setSize: (state, action: PayloadAction<number>) => ({
      ...state,
      page: initialState.page,
      size: action.payload,
    }),
  },
  extraReducers: {
    [HYDRATE]: (state, action) => ({
      ...state,
      ...action.payload.user,
    }),
  },
});

export const { assignToken, setUser, setPage } = userSlice.actions;

export const selectUserToken = (state: AppState) => state.user.token;

export const selectUserFilters = (state: AppState): UsersListParams => ({
  page: state.user.page,
  size: state.user.size,
  user: state.user.user,
});

export const { reducer } = userSlice;
