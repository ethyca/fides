/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { AccessToken } from "./AccessToken";
import type { UserResponse } from "./UserResponse";

/**
 * Similar to UserResponse except with an access token
 */
export type UserLoginResponse = {
  user_data: UserResponse;
  token_data: AccessToken;
};
