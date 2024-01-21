console.log(`babelrc loading... process.env.NODE_ENV=${process.env.NODE_ENV}`);
module.exports = {
  presets: ["next/babel"],
  plugins: process.env.NODE_ENV == "test" ? ["istanbul"] : [],
};
