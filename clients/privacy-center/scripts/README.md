## Scripts

This directory contains JS files that are not part of the built app, but are
used during build or some other development step.

Note that these scripts aren't written TS because that would require a
compilation step for code that runs within Node, which isn't very convenient.
However, we can use JSDoc comments to provide basic TS support:
https://www.typescriptlang.org/docs/handbook/jsdoc-supported-types.html#types-1
