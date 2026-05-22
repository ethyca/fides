/**
 * Jest global setup: mock crypto.randomUUID for jsdom environment.
 * jsdom provides crypto.getRandomValues but not crypto.randomUUID.
 * This must run before any test modules are imported so that module-level
 * calls to crypto.randomUUID() (e.g. in cookie.ts) use the mock.
 *
 * Returns a deterministic sequence of UUIDs. The first value matches the
 * MOCK_UUID used across cookie and tcf tests. Subsequent calls return
 * unique values so lifecycle manager tests still work correctly.
 */
const MOCK_UUIDS = [
  "fae7e16d-37fd-40ed-b2a8-a020ad90106d",
  "11111111-1111-4111-8111-111111111111",
  "22222222-2222-4222-8222-222222222222",
  "33333333-3333-4333-8333-333333333333",
  "44444444-4444-4444-8444-444444444444",
];
let uuidIndex = 0;
globalThis.crypto.randomUUID = (() => {
  const uuid = MOCK_UUIDS[uuidIndex % MOCK_UUIDS.length];
  uuidIndex += 1;
  return uuid;
}) as typeof globalThis.crypto.randomUUID;
