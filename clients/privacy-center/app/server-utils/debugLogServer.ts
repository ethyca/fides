/**
 * debugLogServer: just a wrapper for console.debug without the need for the eslint exception
 * This is a workaround because fidesDebugger is not working on productions builds. Once
 * the issue is resolved we should use fidesDebugger instead.
 */

// eslint-disable-next-line no-console
const debugLogServer = console.debug;
export default debugLogServer;
