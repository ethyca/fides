// Helper functions to determine UI visibility - extracted for testability

/**
 * Helper function to check if password login is enabled based on system settings
 * and user preferences.
 */
const isPasswordLoginEnabled = (
  isPlusEnabled: boolean,
  ssoEnabled: boolean,
  allowUsernameAndPassword: boolean | undefined,
  passwordLoginEnabled?: boolean | null,
): boolean => {
  return (
    !isPlusEnabled ||
    (isPlusEnabled && !ssoEnabled) ||
    (isPlusEnabled &&
      ssoEnabled &&
      allowUsernameAndPassword === true &&
      !!passwordLoginEnabled)
  );
};

export const shouldShowPasswordLoginToggle = (
  isPlusEnabled: boolean,
  ssoEnabled: boolean,
  allowUsernameAndPassword: boolean | undefined,
): boolean => {
  // Only show password login toggle if:
  // - Plus is enabled (prerequisite for SSO)
  // - SSO is enabled (prerequisite for password login option)
  // - Username/password login is allowed as an option
  return Boolean(isPlusEnabled && ssoEnabled && allowUsernameAndPassword);
};

export const shouldShowPasswordField = (
  isNewUser: boolean,
  inviteUsersViaEmail: boolean,
  isPlusEnabled: boolean,
  ssoEnabled: boolean,
  allowUsernameAndPassword: boolean | undefined,
  passwordLoginEnabled?: boolean | null,
): boolean => {
  // Only show password field for new users who aren't invited by email
  if (!isNewUser || inviteUsersViaEmail) {
    return false;
  }

  // Use shared logic to check if password login is available
  return isPasswordLoginEnabled(
    isPlusEnabled,
    ssoEnabled,
    allowUsernameAndPassword,
    passwordLoginEnabled,
  );
};

export const shouldShowPasswordManagement = (
  isPlusEnabled: boolean,
  ssoEnabled: boolean,
  allowUsernameAndPassword: boolean | undefined,
  passwordLoginEnabled?: boolean | null,
): boolean => {
  // Use shared logic to check if password login is available
  return isPasswordLoginEnabled(
    isPlusEnabled,
    ssoEnabled,
    allowUsernameAndPassword,
    passwordLoginEnabled,
  );
};
