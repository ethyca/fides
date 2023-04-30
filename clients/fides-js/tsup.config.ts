/* eslint-disable import/no-extraneous-dependencies */
import { Format, defineConfig } from "tsup";

// TODO: this felt nice at first, but I'm feeling like rollup is a safer choice
// - it's *designed* for the browser, whereas tsup I have to do tricks like the
// noExternal/platform configs to make it browser-compatible... and now I'm
// noticing that I can't *only* minify the .js output and keep the .mjs legible,
// etc.
// TL;DR: switch back to rollup

// Define the configuration used to bundle the fides-js package using `tsup`
export default defineConfig({
    entry: ["src/fides.ts"],
    dts: true,
    format: ["esm", "iife"],
    minify: true,
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
    platform: "browser",
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