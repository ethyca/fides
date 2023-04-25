/* eslint-disable import/no-extraneous-dependencies */
import { Format, defineConfig } from "tsup";

// Define the configuration used to bundle the fides-js package using `tsup`
export default defineConfig({
    entry: ["src/fides.ts"],
    dts: true,
    format: ["esm", "iife"],
    outExtension({ format }) {
        const outfile: Record<Format, string> = {
            "esm": ".mjs",
            "iife": ".js",
            "cjs": ".cjs",
        }
        return {
            js: outfile[format]
        }
    },
    // NOTE: tsup behaves differently from other bundlers like rollup in that it
    // *doesn't* bundle dependencies in the ESM module (dist/fides.mjs).
    //
    // This creates some complexity when importing this module into other local
    // packages since they need to be able to resolve all dependencies
    // themselves - that tends to work for Typescript / Turborepo tooling, but
    // we ran into issues with Jest trying to resolve everything.
    //
    // Therefore, we bundle *everything* into the tsup output, including what
    // would otherwise be "external" dependencies.
    // See discussion here: https://github.com/egoist/tsup/issues/619
    noExternal: [/(.*)/],
})