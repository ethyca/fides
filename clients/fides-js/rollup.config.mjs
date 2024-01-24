/* eslint-disable import/no-extraneous-dependencies */
import alias from "@rollup/plugin-alias";
import copy from "rollup-plugin-copy";
import dts from "rollup-plugin-dts";
import esbuild from "rollup-plugin-esbuild";
import filesize from "rollup-plugin-filesize";
import json from "@rollup/plugin-json";
import nodeResolve from "@rollup/plugin-node-resolve";
import postcss from "rollup-plugin-postcss";

const IS_DEV = process.env.NODE_ENV === "development";

// Define some constants for each of our script bundles
const NAME = "fides";
const SCRIPTS = [
  // 1) fides.js
  {
    name: NAME,
    gzipWarnSizeKb: 15,
    gzipErrorSizeKb: 24,
  },
  // 2) fides-tcf.js
  {
    name: `${NAME}-tcf`,
    gzipWarnSizeKb: 35,
    gzipErrorSizeKb: 43,
  },
  // 3) fides-ext-gpp.js
  {
    name: `${NAME}-ext-gpp`,
    gzipWarnSizeKb: 10,
    gzipErrorSizeKb: 15,
    isExtension: true,
  },
];

// Alias usages of React to use Preact instead
const preactAliases = {
  entries: [
    { find: "react", replacement: "preact/compat" },
    { find: "react-dom/test-utils", replacement: "preact/test-utils" },
    { find: "react-dom", replacement: "preact/compat" },
    { find: "react/jsx-runtime", replacement: "preact/jsx-runtime" },
  ],
};

// Define the core plugins used for all the FidesJS script bundles
const fidesScriptPlugins = ({ name, gzipWarnSizeKb, gzipErrorSizeKb }) => [
  alias(preactAliases),
  nodeResolve(),
  json(),
  postcss({
    minimize: !IS_DEV,
  }),
  esbuild({
    minify: !IS_DEV,
  }),
  copy({
    // Automatically add the built script to the privacy center's static files for bundling:
    targets: [
      {
        src: `dist/${name}.js`,
        dest: `../privacy-center/public/lib/`,
      },
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
        if (gzipSizeKb > gzipErrorSizeKb) {
          console.error(
            `❌ ERROR: ${fileName} build failed! Gzipped size (${gzipSize}) exceeded maximum size (${gzipErrorSizeKb} KB)!`,
            `If you must, update GZIP_SIZE_* constants in clients/fides-js/rollup.config.mjs`
          );
          process.exit(1);
        } else if (gzipSizeKb > gzipWarnSizeKb) {
          console.warn(
            `️🚨 WARN: ${fileName} build is getting large! Gzipped size (${gzipSize}) exceeded warning size (${gzipWarnSizeKb} KB)!`,
            `If you must, update GZIP_SIZE_* constants in clients/fides-js/rollup.config.mjs`
          );
          if (IS_DEV) {
            process.exit(1);
          }
        } else {
          console.log(
            `✅ ${fileName} gzipped size passed maximum size checks (${gzipSize} < ${gzipErrorSizeKb} KB)`
          );
        }
      },
    ],
  }),
];

/**
 * @type {import('rollup').RollupOptions}
 */
const rollupOptions = [];

SCRIPTS.forEach(({ name, gzipErrorSizeKb, gzipWarnSizeKb, isExtension }) => {
  const js = {
    input: `src/${name}.ts`,
    plugins: fidesScriptPlugins({
      name,
      gzipWarnSizeKb,
      gzipErrorSizeKb,
    }),
    output: [
      {
        // Intended for browser <script> tag - defines `Fides` global. Also supports UMD loaders.
        file: `dist/${name}.js`,
        name: isExtension ? undefined : "Fides",
        format: isExtension ? undefined : "umd",
        sourcemap: IS_DEV,
      },
    ],
  };
  const mjs = {
    input: `src/${name}.ts`,
    plugins: [
      alias(preactAliases),
      json(),
      nodeResolve(),
      postcss(),
      esbuild(),
    ],
    output: [
      {
        // Compatible with ES module imports. Apps in this repo may be able to share the code.
        file: `dist/${name}.mjs`,
        format: "es",
        sourcemap: true,
      },
    ],
  };
  const declaration = {
    input: `src/${name}.ts`,
    plugins: [dts(), postcss()],
    output: [
      {
        file: `dist/${name}.d.ts`,
      },
    ],
  };

  rollupOptions.push(...[js, mjs, declaration]);
});

export default rollupOptions;
