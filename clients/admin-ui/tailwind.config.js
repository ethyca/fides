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
          1: "var(--fidesui-neutral-50)",
          2: "var(--fidesui-neutral-100)",
          3: "var(--fidesui-neutral-200)",
          4: "var(--fidesui-neutral-300)",
          5: "var(--fidesui-neutral-400)",
          6: "var(--fidesui-neutral-500)",
          7: "var(--fidesui-neutral-600)",
          8: "var(--fidesui-neutral-700)",
          9: "var(--fidesui-neutral-800)",
          10: "var(--fidesui-neutral-900)",
        },
      },
    },
  },
  plugins: [],
};
