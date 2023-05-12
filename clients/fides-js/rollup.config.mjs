/* eslint-disable import/no-extraneous-dependencies */
import alias from "@rollup/plugin-alias";
import commonjs from "@rollup/plugin-commonjs";
import copy from "rollup-plugin-copy";
import dts from "rollup-plugin-dts";
import esbuild from "rollup-plugin-esbuild";
import filesize from "rollup-plugin-filesize";
import nodeResolve from "@rollup/plugin-node-resolve";
import css from "rollup-plugin-import-css";

const name = "fides";
const isDev = process.env.NODE_ENV === "development";
const GZIP_SIZE_ERROR_KB = 20; // fail build if bundle size exceeds this
const GZIP_SIZE_WARN_KB = 15; // log a warning if bundle size exceeds this

/**
 * @type {import('rollup').RollupOptions}
 */
export default [
  {
    input: `src/${name}.ts`,
    // DEFER: Add aliases for typical react imports (see https://preactjs.com/guide/v10/getting-started/#aliasing-in-rollup)
    // This will be needed if & when we want to leverage other packages written for the React ecosystem
    plugins: [
      alias({
        entries: [
          { find: "react", replacement: "preact/compat" },
          { find: "react-dom/test-utils", replacement: "preact/test-utils" },
          { find: "react-dom", replacement: "preact/compat" },
          { find: "react/jsx-runtime", replacement: "preact/jsx-runtime" },
        ],
      }),
      nodeResolve(),
      commonjs({
        include: "../node_modules",
      }),
      css(),
      esbuild({
        minify: !isDev,
      }),
      copy({
        // Automatically add the built script to the privacy center's static files for bundling:
        targets: [
          { src: `dist/${name}.js`, dest: "../privacy-center/public/lib/" },
        ],
        verbose: true,
        hook: "writeBundle",
      }),
      copy({
        // Automatically add the built css to the privacy center's static files for bundling:
        targets: [
          { src: `dist/${name}.css`, dest: "../privacy-center/public/lib/" },
        ],
        verbose: true,
        hook: "writeBundle",
      }),
      filesize({
        reporter: [
          "boxen", // default reporter, which prints a nice CLI output

          // Add a defensive check to fail the build if our bundle size starts getting too big!
          (options, bundle, { gzipSize, fileName }) => {
            const gzipSizeKb = Number(gzipSize.replace(" KB", ""));
            if (gzipSizeKb > GZIP_SIZE_ERROR_KB) {
              console.error(
                `❌ ERROR: ${fileName} build failed! Gzipped size (${gzipSize}) exceeded maximum size (${GZIP_SIZE_ERROR_KB} KB)!`,
                `If you must, update GZIP_SIZE_* constants in clients/fides-js/rollup.config.mjs`
              );
              process.exit(1);
            } else if (gzipSizeKb > GZIP_SIZE_WARN_KB) {
              console.warn(
                `️🚨 WARN: ${fileName} build is getting large! Gzipped size (${gzipSize}) exceeded warning size (${GZIP_SIZE_WARN_KB} KB)!`,
                `If you must, update GZIP_SIZE_* constants in clients/fides-js/rollup.config.mjs`
              );
              if (isDev) {
                process.exit(1);
              }
            } else {
              console.log(
                `✅ ${fileName} gzipped size passed maximum size checks (${gzipSize} < ${GZIP_SIZE_ERROR_KB} KB)`
              );
            }
          },
        ],
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
    input: `src/${name}.ts`,
    plugins: [nodeResolve(), css(), esbuild()],
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
    input: `src/${name}.ts`,
    plugins: [dts(), css()],
    output: [
      {
        file: `dist/${name}.d.ts`,
      },
    ],
  },
];
