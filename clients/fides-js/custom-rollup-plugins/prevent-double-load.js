/**
 * Rollup plugin to prevent double loading of Fides scripts
 */
export const preventDoubleLoad = (globalName) => {
  const multipleLoadingMessage = `${globalName} detected that it was already loaded on this page, aborting execution! See https://www.ethyca.com/docs/dev-docs/js/troubleshooting for more information.`;

  // Common replacement pattern for all UMD wrappers
  const doubleLoadCheck = `if(typeof ${globalName}!=="undefined" && ${globalName}.options && ${globalName}.options.fidesUnsupportedRepeatedScriptLoading !== "enabled_acknowledge_not_supported"){console.error("${multipleLoadingMessage}");return;}`;

  // Define UMD wrapper patterns to match
  const umdPatterns = [
    {
      name: "Standard UMD wrapper (unminified)",
      regex: /(\(function \(global, factory\) \{)/,
    },
    {
      name: "Minified UMD wrapper with complete factory pattern",
      regex:
        /(\(function\([a-zA-Z0-9_$]+,[a-zA-Z0-9_$]+\)\{[^}]*\}\)\(this,function\([a-zA-Z0-9_$]+\)\{)/,
    },
    {
      name: "Generic function start pattern",
      regex: /^(\(function\([^)]+\)\{)/,
    },
  ];

  const tryReplaceWithPattern = (code, pattern) => {
    const replacement = `$1${doubleLoadCheck}`;
    const replaced = code.replace(pattern.regex, replacement);
    return replaced !== code ? replaced : null;
  };

  return {
    name: "prevent-double-load",
    generateBundle(options, bundle) {
      Object.keys(bundle).forEach((fileName) => {
        const chunk = bundle[fileName];
        if (chunk.type === "chunk" && options.format === "umd") {
          let wasReplaced = false;

          // Try each pattern until one succeeds
          for (const pattern of umdPatterns) {
            const replaced = tryReplaceWithPattern(chunk.code, pattern);
            if (replaced) {
              chunk.code = replaced;
              wasReplaced = true;
              break;
            }
          }

          if (!wasReplaced) {
            console.warn(
              `[prevent-double-load] Could not find UMD wrapper pattern in ${fileName} to inject double-load prevention code`,
            );
          }
        }
      });
    },
  };
};
