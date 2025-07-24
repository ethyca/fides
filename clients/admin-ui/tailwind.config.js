/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        // TODO: unify with existing Tailwind "gray" color
        neutral: {
          1: "#fafafa",
          2: "#e6e6e8",
          3: "#d1d2d4",
          4: "#bcbec1",
          5: "#a8aaad",
          6: "#93969a",
          7: "#7e8185",
          8: "#696c71",
          9: "#53575c",
          10: "#2b2e35",
        },
      },
    },
  },
  plugins: [],
};
