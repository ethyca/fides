import alias from "@rollup/plugin-alias";
import copy from "rollup-plugin-copy";
import dts from "rollup-plugin-dts";
import esbuild from "rollup-plugin-esbuild";
import filesize from "rollup-plugin-filesize";
import json from "@rollup/plugin-json";
import nodeResolve from "@rollup/plugin-node-resolve";
import postcss from "rollup-plugin-postcss";
import commonjs from "@rollup/plugin-commonjs";
import { visualizer } from "rollup-plugin-visualizer";
import strip from "@rollup/plugin-strip";

const NAME = "fides";
const IS_DEV = process.env.NODE_ENV === "development";
const GZIP_SIZE_ERROR_KB = 45; // fail build if bundle size exceeds this
const GZIP_SIZE_WARN_KB = 35; // log a warning if bundle size exceeds this

// TCF
const GZIP_SIZE_TCF_ERROR_KB = 87;
const GZIP_SIZE_TCF_WARN_KB = 75;

// Headless
const GZIP_SIZE_HEADLESS_ERROR_KB = 25;
const GZIP_SIZE_HEADLESS_WARN_KB = 20;

// GPP
const GZIP_SIZE_GPP_ERROR_KB = 25;
const GZIP_SIZE_GPP_WARN_KB = 15;

const preactAliases = {
  entries: [
    { find: "react", replacement: "preact/compat" },
    { find: "react-dom/test-utils", replacement: "preact/test-utils" },
    { find: "react-dom", replacement: "preact/compat" },
    { find: "react/jsx-runtime", replacement: "preact/jsx-runtime" },
  ],
};

const fidesScriptPlugins = ({ name, gzipWarnSizeKb, gzipErrorSizeKb }) => [
  alias(preactAliases),
  nodeResolve(),
  commonjs(),
  json(),
  postcss({
    minimize: !IS_DEV,
  }),
  esbuild({
    minify: !IS_DEV,
  }),
  strip(
    IS_DEV
      ? {}
      : {
          include: ["**/*.ts"],
          functions: ["fidesDebugger"],
        },
  ),
  copy({
    // Automatically add the built script to the privacy center's and admin ui's static files for bundling:
    targets: [
      {
        src: `dist/${name}.js`,
        dest: `../privacy-center/public/lib/`,
      },
      {
        src: `dist/${name}.js`,
        dest: `../admin-ui/public/lib/`,
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
        if (gzipSizeKb > gzipErrorSizeKb && !IS_DEV) {
          console.error(
            `❌ ERROR: ${fileName} build failed! Gzipped size (${gzipSize}) exceeded maximum size (${gzipErrorSizeKb} KB)!`,
            `If you must, update GZIP_SIZE_* constants in clients/fides-js/rollup.config.mjs.`,
            `Open bundle-size-stats/${name}-stats.html to visualize the (non-gzipped) bundle size.`,
          );
          process.exit(1);
        } else if (gzipSizeKb > gzipWarnSizeKb && !IS_DEV) {
          console.warn(
            `️🚨 WARN: ${fileName} build is getting large! Gzipped size (${gzipSize}) exceeded warning size (${gzipWarnSizeKb} KB)!`,
            `If you must, update GZIP_SIZE_* constants in clients/fides-js/rollup.config.mjs.`,
            `Open bundle-size-stats/${name}-stats.html to visualize the (non-gzipped) bundle size.`,
          );
        } else {
          console.log(
            `✅ ${fileName} gzipped size passed maximum size checks (${gzipSize} < ${gzipErrorSizeKb} KB)`,
          );
        }
      },
    ],
  }),
  visualizer({
    filename: `bundle-size-stats/${name}-stats.html`,
  }),
];

const SCRIPTS = [
  {
    name: NAME,
    gzipWarnSizeKb: GZIP_SIZE_WARN_KB,
    gzipErrorSizeKb: GZIP_SIZE_ERROR_KB,
  },
  {
    name: `${NAME}-tcf`,
    gzipWarnSizeKb: GZIP_SIZE_TCF_WARN_KB,
    gzipErrorSizeKb: GZIP_SIZE_TCF_ERROR_KB,
  },
  {
    name: `${NAME}-headless`,
    gzipWarnSizeKb: GZIP_SIZE_HEADLESS_WARN_KB,
    gzipErrorSizeKb: GZIP_SIZE_HEADLESS_ERROR_KB,
  },
  {
    name: `${NAME}-ext-gpp`,
    gzipWarnSizeKb: GZIP_SIZE_GPP_WARN_KB,
    gzipErrorSizeKb: GZIP_SIZE_GPP_ERROR_KB,
    isExtension: true,
  },
];

/**
 * @type {import('rollup').RollupOptions}
 */
const rollupOptions = [];

/**
 * For each of our entrypoint scripts, build .js, .mjs, and .d.ts outputs
 */
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
        sourcemap: IS_DEV && !isExtension ? "inline" : false,
      },
    ],
  };
  const mjs = {
    input: `src/${name}.ts`,
    plugins: [
      alias(preactAliases),
      json(),
      nodeResolve(),
      commonjs(),
      postcss(),
      esbuild(),
      strip({
        include: ["**/*.js", "**/*.ts"],
        functions: ["fidesDebugger"],
      }),
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

/**
 * In addition to our regular built outputs (like fides.js!) also generate a
 * fides-types.d.ts file from  our documented types for external use.
 */
rollupOptions.push({
  input: `src/docs/index.ts`,
  plugins: [dts()],
  output: [
    {
      file: `dist/fides-types.d.ts`,
    },
  ],
});

export default rollupOptions;
