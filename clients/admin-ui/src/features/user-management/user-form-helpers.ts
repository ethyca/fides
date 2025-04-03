// Helper functions to determine UI visibility - extracted for testability
export const shouldShowLoginMethodSelector = (
  isPlusEnabled: boolean,
  ssoEnabled: boolean,
  allowUsernameAndPassword: boolean | undefined,
): boolean => {
  // Only show login method selector if:
  // - Plus is enabled (prerequisite for SSO)
  // - SSO is enabled (prerequisite for username/password option)
  // - Username/password login is allowed as an option
  return Boolean(isPlusEnabled && ssoEnabled && allowUsernameAndPassword);
};

export const shouldShowPasswordField = (
  isNewUser: boolean,
  inviteUsersViaEmail: boolean,
  isPlusEnabled: boolean,
  ssoEnabled: boolean,
  allowUsernameAndPassword: boolean | undefined,
  loginMethod?: string | null,
): boolean => {
  // Only show password field for new users who aren't invited by email
  if (!isNewUser || inviteUsersViaEmail) {
    return false;
  }

  // Show password field if:
  // - Plus is not enabled, OR
  // - Plus is enabled but SSO is not enabled, OR
  // - Plus is enabled with SSO, username/password login is allowed and selected
  return (
    !isPlusEnabled ||
    (isPlusEnabled && !ssoEnabled) ||
    (isPlusEnabled &&
      ssoEnabled &&
      allowUsernameAndPassword === true &&
      loginMethod === "username_password")
  );
};

export const shouldShowPasswordManagement = (
  isPlusEnabled: boolean,
  ssoEnabled: boolean,
  allowUsernameAndPassword: boolean | undefined,
  loginMethod?: string | null,
): boolean => {
  // Only show password management if:
  // - Plus is not enabled, OR
  // - Plus is enabled but SSO is not enabled, OR
  // - Plus is enabled with SSO, username/password login is allowed and selected
  return (
    !isPlusEnabled ||
    (isPlusEnabled && !ssoEnabled) ||
    (isPlusEnabled &&
      ssoEnabled &&
      allowUsernameAndPassword === true &&
      loginMethod === "username_password")
  );
};

export const isPasswordFieldRequired = (
  isNewUser: boolean,
  inviteUsersViaEmail: boolean,
  isPlusEnabled: boolean,
  ssoEnabled: boolean,
  allowUsernameAndPassword: boolean | undefined,
  loginMethod?: string | null,
): boolean => {
  // Password field is required if:
  // - Configuring a new user, AND
  // - Users aren't being invited by email, AND
  // - One of the following is true:
  //   - Plus is not enabled, OR
  //   - Plus is enabled but SSO is not enabled, OR
  //   - Plus is enabled with SSO, username/password login is allowed and selected

  if (!isNewUser || inviteUsersViaEmail) {
    return false;
  }

  return (
    !isPlusEnabled ||
    (isPlusEnabled && !ssoEnabled) ||
    (isPlusEnabled &&
      ssoEnabled &&
      allowUsernameAndPassword === true &&
      loginMethod === "username_password")
  );
};
