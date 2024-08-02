import { User } from "user-management/types";

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginWithOIDCRequest {
  provider: string;
  code: string;
}

export interface LoginResponse {
  user_data: User;
  token_data: {
    access_token: string;
  };
}

export interface LogoutRequest {}
export interface LogoutResponse {}
