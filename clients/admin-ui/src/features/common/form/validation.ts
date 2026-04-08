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
