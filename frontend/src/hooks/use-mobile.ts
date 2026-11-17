import * as React from "react";

const MOBILE_BREAKPOINT = 768;

function subscribe(onStoreChange: () => void) {
  const mql = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`);
  mql.addEventListener("change", onStoreChange);
  return () => mql.removeEventListener("change", onStoreChange);
}

function getSnapshot() {
  return window.innerWidth < MOBILE_BREAKPOINT;
}

// No viewport on the server; report desktop so hydration matches, then React
// re-renders with the client snapshot.
function getServerSnapshot() {
  return false;
}

export function useIsMobile() {
  return React.useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}
