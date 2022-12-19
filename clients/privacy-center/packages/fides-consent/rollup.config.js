import copy from "rollup-plugin-copy";
import dts from "rollup-plugin-dts";
import esbuild from "rollup-plugin-esbuild";
import nodeResolve from "@rollup/plugin-node-resolve";

const name = require("./package.json").name;

const isDev = process.env.NODE_ENV === "development";

export default [
  {
    input: `src/${name}.ts`,
    plugins: [
      nodeResolve(),
      esbuild({
        minify: !isDev,
      }),
      copy({
        // Automatically add the built script to the privacy center's static files for testing:
        targets: [{ src: `dist/${name}.js`, dest: "../../public/" }],
        verbose: true,
        hook: "writeBundle",
      }),
    ],
    output: [
      {
        // Intended for browser <script> tag - defines `Fides` global. Also supports UMD loaders.
        file: `dist/${name}.js`,
        name: "Fides",
        format: "umd",
        sourcemap: isDev,
      },
    ],
  },
  {
    input: `src/lib/index.ts`,
    plugins: [nodeResolve(), esbuild()],
    output: [
      {
        // Compatible with ES module imports. Apps in this repo may be able to share the code.
        file: `dist/${name}.mjs`,
        format: "es",
        sourcemap: true,
      },
    ],
  },
  {
    input: `src/lib/index.ts`,
    plugins: [dts()],
    output: [
      {
        file: `dist/${name}.d.ts`,
      },
    ],
  },
];
