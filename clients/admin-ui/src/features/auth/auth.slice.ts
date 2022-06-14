import {
  createListenerMiddleware,
  createSlice,
  PayloadAction,
} from '@reduxjs/toolkit';
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

import type { RootState } from '../../app/store';
import { BASE_API_URN, STORED_CREDENTIALS_KEY } from '../../constants';
import { User } from '../user-management/types';
import { LoginRequest, LoginResponse } from './types';

export interface AuthState {
  user: User | null;
  token: string | null;
}

const initialState: AuthState = {
  token: null,
  user: null,
};

// Auth slice
export const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    login(
      state,
      { payload: { user_data, token_data } }: PayloadAction<LoginResponse>
    ) {
      return Object.assign(state, {
        user: user_data,
        token: token_data.access_token,
      });
    },
    logout(state) {
      return Object.assign(state, {
        user: null,
        token: null,
      });
    },
  },
});

export const selectAuth = (state: RootState) => state.auth;
export const selectUser = (state: RootState) => selectAuth(state).user;
export const selectToken = (state: RootState) => selectAuth(state).token;

export const { login, logout } = authSlice.actions;

export const credentialStorage = createListenerMiddleware();
credentialStorage.startListening({
  actionCreator: login,
  effect: (action, { getState }) => {
    if (window && window.localStorage) {
      localStorage.setItem(
        STORED_CREDENTIALS_KEY,
        JSON.stringify(selectAuth(getState() as RootState))
      );
    }
  },
});
credentialStorage.startListening({
  actionCreator: logout,
  effect: () => {
    if (window && window.localStorage) {
      localStorage.removeItem(STORED_CREDENTIALS_KEY);
    }
  },
});

// Auth API
export const authApi = createApi({
  reducerPath: 'authApi',
  baseQuery: fetchBaseQuery({
    baseUrl: BASE_API_URN,
    prepareHeaders: (headers, { getState }) => {
      const token = selectToken(getState() as RootState);
      headers.set('Access-Control-Allow-Origin', '*');
      if (token) {
        headers.set('authorization', `Bearer ${token}`);
      }
      return headers;
    },
  }),
  tagTypes: ['Auth'],
  endpoints: (build) => ({
    login: build.mutation<LoginResponse, LoginRequest>({
      query: (credentials) => ({
        url: 'login',
        method: 'POST',
        body: credentials,
      }),
      invalidatesTags: () => ['Auth'],
    }),
  }),
});

export const { useLoginMutation } = authApi;
export const { reducer } = authSlice;
