import { useSyncExternalStore } from "react";

const subscribe = () => () => {};
const getSnapshot = () => true;
const getServerSnapshot = () => false;

/**
 * False on the server and during hydration, true on the client afterwards.
 *
 * Use it to render client-only UI (localStorage, theme, viewport) without a
 * hydration mismatch, instead of a `setMounted(true)` effect.
 */
export function useIsHydrated(): boolean {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}
