import alias from "@rollup/plugin-alias";
import copy from "rollup-plugin-copy";
import dts from "rollup-plugin-dts";
import esbuild, { minify } from "rollup-plugin-esbuild";
import filesize from "rollup-plugin-filesize";
import json from "@rollup/plugin-json";
import nodeResolve from "@rollup/plugin-node-resolve";
import postcss from "rollup-plugin-postcss";
import commonjs from "@rollup/plugin-commonjs";
import { visualizer } from "rollup-plugin-visualizer";
import strip from "@rollup/plugin-strip";
import replace from "@rollup/plugin-replace";
import fs from "fs";
import jsxRemoveAttributes from "rollup-plugin-jsx-remove-attributes";
import { importFidesPackageVersion } from "../build-utils.js";

const GLOBAL_NAME = "Fides";
const FILE_NAME = "fides";
const IS_DEV = process.env.NODE_ENV === "development";
const IS_TEST = process.env.IS_TEST === "true";
const GZIP_SIZE_ERROR_KB = 50; // fail build if bundle size exceeds this
const GZIP_SIZE_WARN_KB = 45; // log a warning if bundle size exceeds this

// TCF
const GZIP_SIZE_TCF_ERROR_KB = 95;
const GZIP_SIZE_TCF_WARN_KB = 75;

// Headless
const GZIP_SIZE_HEADLESS_ERROR_KB = 25;
const GZIP_SIZE_HEADLESS_WARN_KB = 20;

// GPP
const GZIP_SIZE_GPP_ERROR_KB = 40;
const GZIP_SIZE_GPP_WARN_KB = 35;

const multipleLoadingMessage = `${GLOBAL_NAME} detected that it was already loaded on this page, aborting execution! See https://www.ethyca.com/docs/dev-docs/js/troubleshooting for more information.`;

const preactAliases = {
  entries: [
    { find: "react", replacement: "preact/compat" },
    { find: "react-dom/test-utils", replacement: "preact/test-utils" },
    { find: "react-dom", replacement: "preact/compat" },
    { find: "react/jsx-runtime", replacement: "preact/jsx-runtime" },
  ],
};

const fidesScriptPlugins = (stripDebugger = false) => [
  alias(preactAliases),
  nodeResolve(),
  commonjs(),
  json(),
  postcss({
    minimize: !IS_DEV,
  }),
  esbuild(),
  !IS_DEV && !IS_TEST && jsxRemoveAttributes(), // removes `data-testid`
  (!IS_DEV || stripDebugger) &&
    strip({
      include: ["**/*.ts", "**/*.tsx"],
      functions: ["fidesDebugger"],
    }),
  !IS_DEV && minify(),
  replace({
    // version.json is created by the docker build process and contains the versioneer version
    __RELEASE_VERSION__: () => importFidesPackageVersion(),
    preventAssignment: true,
    include: ["src/lib/init-utils.ts"],
  }),
];

const fidesScriptsJSPlugins = ({ name, gzipWarnSizeKb, gzipErrorSizeKb }) => [
  ...fidesScriptPlugins(),
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
    name: FILE_NAME,
    gzipWarnSizeKb: GZIP_SIZE_WARN_KB,
    gzipErrorSizeKb: GZIP_SIZE_ERROR_KB,
  },
  {
    name: `${FILE_NAME}-tcf`,
    gzipWarnSizeKb: GZIP_SIZE_TCF_WARN_KB,
    gzipErrorSizeKb: GZIP_SIZE_TCF_ERROR_KB,
  },
  {
    name: `${FILE_NAME}-headless`,
    gzipWarnSizeKb: GZIP_SIZE_HEADLESS_WARN_KB,
    gzipErrorSizeKb: GZIP_SIZE_HEADLESS_ERROR_KB,
  },
  {
    name: `${FILE_NAME}-ext-gpp`,
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
 * Ignore circular dependency warnings from node_modules
 * that we don't control.
 */
const onLog = (_, { code, message }) => {
  if (code === "CIRCULAR_DEPENDENCY" && message.includes("node_modules")) {
    return;
  }
};

/**
 * For each of our entrypoint scripts, build .js, .mjs, and .d.ts outputs
 */
SCRIPTS.forEach(({ name, gzipErrorSizeKb, gzipWarnSizeKb, isExtension }) => {
  const js = {
    input: `src/${name}.ts`,
    plugins: fidesScriptsJSPlugins({
      name,
      gzipWarnSizeKb,
      gzipErrorSizeKb,
    }),
    output: [
      {
        // Intended for browser <script> tag - defines `Fides` global. Also supports UMD loaders.
        file: `dist/${name}.js`,
        name: isExtension ? undefined : GLOBAL_NAME,
        format: isExtension ? "es" : "umd",
        sourcemap: IS_DEV ? "inline" : false,
        amd: {
          define: undefined, // prevent the bundle from registering itself as an AMD module, even if an AMD loader (like RequireJS) is present on the page. This allows FidesJS to use Rollup's `umd` format to support both `iife` and `cjs` modules, but excludes AMD.
        },
        banner: isExtension
          ? undefined
          : `(function(){if(typeof ${GLOBAL_NAME}==="undefined" || (${GLOBAL_NAME}.options && ${GLOBAL_NAME}.options.fidesUnsupportedRepeatedScriptLoading === "enabled_acknowledge_not_supported")) {`,
        footer: isExtension
          ? undefined
          : `} else {
          console.error("${multipleLoadingMessage}");
        }})()`,
      },
    ],
    onLog,
  };
  const mjs = {
    input: `src/${name}.ts`,
    plugins: fidesScriptPlugins(true),
    output: [
      {
        // Compatible with ES module imports. Apps in this repo may be able to share the code.
        file: `dist/${name}.mjs`,
        format: "es",
        sourcemap: true,
      },
    ],
    onLog,
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

// Add preview script build configuration
const previewScript = {
  input: "src/fides-preview.ts",
  plugins: [
    esbuild({
      minify: true,
    }),
    replace({
      // Inject the actual script contents during build
      // These will be properly escaped as strings
      FIDES_STANDARD_SCRIPT: () => {
        const standardPath = "dist/fides.js";
        return JSON.stringify(fs.readFileSync(standardPath, "utf-8"));
      },
      FIDES_TCF_SCRIPT: () => {
        const tcfPath = "dist/fides-tcf.js";
        return JSON.stringify(fs.readFileSync(tcfPath, "utf-8"));
      },
      preventAssignment: true,
    }),
    copy({
      targets: [
        {
          src: "dist/fides-preview.js",
          dest: "../admin-ui/public/lib/",
        },
      ],
      verbose: true,
      hook: "writeBundle",
    }),
  ],
  output: [
    {
      file: "dist/fides-preview.js",
      format: "umd",
      name: "FidesPreview",
      sourcemap: false,
    },
  ],
};

// Add preview script to build after the main scripts
rollupOptions.push(previewScript);

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
