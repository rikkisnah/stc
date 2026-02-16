// Code was generated via OCI AI and was reviewed by a human SDE
// Tag: #ai-assisted
"use client";

import { useEffect, useRef } from "react";
import { saveSessionState, type SessionState } from "../session-persistence";

const SAVE_INTERVAL_MS = 5_000;

export function useSessionPersistence(getState: () => SessionState | null): void {
  const lastSerializedRef = useRef<string>("");
  const getStateRef = useRef(getState);
  getStateRef.current = getState;

  useEffect(() => {
    const interval = setInterval(() => {
      const state = getStateRef.current();
      if (!state) return;
      const serialized = JSON.stringify(state);
      if (serialized === lastSerializedRef.current) return;
      lastSerializedRef.current = serialized;
      saveSessionState(state);
    }, SAVE_INTERVAL_MS);

    return () => {
      clearInterval(interval);
      // Save on unmount if run is active
      const state = getStateRef.current();
      if (state) {
        saveSessionState(state);
      }
    };
  }, []);
}
