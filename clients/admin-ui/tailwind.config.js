/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["selector", '[data-theme="dark"]'],
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
    "../fidesui/src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "../fidesui/src/hoc/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        neutral: {
          1: "var(--ant-neutral-50)",
          2: "var(--ant-neutral-100)",
          3: "var(--ant-neutral-200)",
          4: "var(--ant-neutral-300)",
          5: "var(--ant-neutral-400)",
          6: "var(--ant-neutral-500)",
          7: "var(--ant-neutral-600)",
          8: "var(--ant-neutral-700)",
          9: "var(--ant-neutral-800)",
          10: "var(--ant-neutral-900)",
        },
      },
    },
  },
  plugins: [],
};
