// Code was generated via OCI AI and was reviewed by a human SDE
// Tag: #ai-assisted
import "@testing-library/jest-dom";

// Polyfill TextEncoder/TextDecoder for jsdom (used by NDJSON streaming)
import { TextEncoder, TextDecoder } from "node:util";

if (typeof globalThis.TextEncoder === "undefined") {
  Object.assign(globalThis, { TextEncoder, TextDecoder });
}
