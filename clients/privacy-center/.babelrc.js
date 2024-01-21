module.exports = {
  presets: ["next/babel"],
  plugins: process.env.NODE_ENV == "test" ? ["istanbul"] : [],
};
