import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { HYDRATE } from 'next-redux-wrapper';

import type { AppState } from '../../app/store';

export interface State {
  token: string | null;
}

const initialState: State = {
  token: null,
};

export const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: {
    assignToken: (state, action: PayloadAction<string>) => ({
      ...state,
      token: action.payload,
    }),
  },
  extraReducers: {
    [HYDRATE]: (state, action) => ({
      ...state,
      ...action.payload.user,
    }),
  },
});

export const { assignToken } = userSlice.actions;

export const selectUserToken = (state: AppState) => state.user.token;

export const { reducer } = userSlice;
