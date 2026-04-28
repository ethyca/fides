export const usernameRules = [
  { required: true, message: "Username is required" },
  { max: 100, message: "Username must be 100 characters or fewer." },
  {
    pattern: /^[a-zA-Z0-9._\-+@]+$/,
    message:
      "Usernames may only contain letters, numbers, and the following characters: . @ + _ -",
  },
];

export const passwordRules = [
  { required: true, message: "Password is required" },
  { min: 8, message: "Password must have at least eight characters." },
  { pattern: /[0-9]/, message: "Password must have at least one number." },
  {
    pattern: /[A-Z]/,
    message: "Password must have at least one capital letter.",
  },
  {
    pattern: /[a-z]/,
    message: "Password must have at least one lowercase letter.",
  },
  { pattern: /[\W_]/, message: "Password must have at least one symbol." },
];

export const isValidURL = (value: string | undefined): boolean => {
  if (
    !value ||
    !(value.startsWith("https://") || value.startsWith("http://"))
  ) {
    return false;
  }
  try {
    // eslint-disable-next-line no-new
    new URL(value);
  } catch {
    return false;
  }
  return true;
};

export const containsNoWildcard = (value: string | undefined): boolean => {
  if (!value) {
    return false;
  }
  return !value.includes("*");
};

export const containsNoPath = (value: string | undefined): boolean => {
  if (!value) {
    return false;
  }
  try {
    const url = new URL(value);
    return url.pathname === "/" && !value.endsWith("/");
  } catch {
    return false;
  }
};

export const corsOriginRules = [
  { required: true, message: "Domain is required" },
  {
    validator: (_: unknown, value: string) => {
      if (!value) {
        return Promise.resolve();
      }
      if (!isValidURL(value)) {
        return Promise.reject(
          new Error("Domain must be a valid URL (e.g. https://example.com)"),
        );
      }
      if (!containsNoWildcard(value)) {
        return Promise.reject(
          new Error(
            "Domain cannot contain a wildcard (e.g. https://*.example.com)",
          ),
        );
      }
      if (!containsNoPath(value)) {
        return Promise.reject(
          new Error(
            "Domain cannot contain a path (e.g. https://example.com/path)",
          ),
        );
      }
      return Promise.resolve();
    },
  },
];
