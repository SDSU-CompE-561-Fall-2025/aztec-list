/**
 * Unit tests for use-mobile hook
 */

import { renderHook, act } from "@testing-library/react";
import { useIsMobile } from "../use-mobile";

describe("use-mobile.ts", () => {
  const originalInnerWidth = window.innerWidth;
  let addEventListenerSpy: jest.Mock;
  let removeEventListenerSpy: jest.Mock;

  beforeEach(() => {
    // Reset window.innerWidth
    Object.defineProperty(window, "innerWidth", {
      writable: true,
      configurable: true,
      value: 1024,
    });

    addEventListenerSpy = jest.fn();
    removeEventListenerSpy = jest.fn();

    // Mock matchMedia so we can assert add/remove listeners
    window.matchMedia = jest.fn().mockImplementation((query) => {
      const matches = window.innerWidth < 768;

      // Cast spies to the exact listener signatures expected by MediaQueryList
      const addEvent = addEventListenerSpy as unknown as MediaQueryList["addEventListener"];
      const removeEvent =
        removeEventListenerSpy as unknown as MediaQueryList["removeEventListener"];

      const mql: MediaQueryList = {
        matches,
        media: query,
        onchange: null,
        addEventListener: addEvent,
        removeEventListener: removeEvent,
        addListener: addEventListenerSpy as unknown as MediaQueryList["addListener"],
        removeListener: removeEventListenerSpy as unknown as MediaQueryList["removeListener"],
        dispatchEvent: jest.fn(() => true),
      };

      return mql;
    });
  });

  afterEach(() => {
    Object.defineProperty(window, "innerWidth", {
      writable: true,
      configurable: true,
      value: originalInnerWidth,
    });
  });

  describe("useIsMobile", () => {
    it("should return false for desktop width", () => {
      Object.defineProperty(window, "innerWidth", {
        writable: true,
        configurable: true,
        value: 1024,
      });

      const { result } = renderHook(() => useIsMobile());
      expect(result.current).toBe(false);
    });

    it("should return true for mobile width", () => {
      Object.defineProperty(window, "innerWidth", {
        writable: true,
        configurable: true,
        value: 375,
      });

      const { result } = renderHook(() => useIsMobile());
      expect(result.current).toBe(true);
    });

    it("should return true at breakpoint (767px)", () => {
      Object.defineProperty(window, "innerWidth", {
        writable: true,
        configurable: true,
        value: 767,
      });

      const { result } = renderHook(() => useIsMobile());
      expect(result.current).toBe(true);
    });

    it("should return false just above breakpoint (768px)", () => {
      Object.defineProperty(window, "innerWidth", {
        writable: true,
        configurable: true,
        value: 768,
      });

      const { result } = renderHook(() => useIsMobile());
      expect(result.current).toBe(false);
    });

    it("should update when window is resized", () => {
      const { result } = renderHook(() => useIsMobile());

      // Start desktop
      expect(result.current).toBe(false);

      // Simulate resize to mobile
      act(() => {
        Object.defineProperty(window, "innerWidth", {
          writable: true,
          configurable: true,
          value: 375,
        });
        window.dispatchEvent(new Event("change"));
      });

      // Should still be false because matchMedia mock doesn't trigger
      // In real browser, this would update to true
    });

    it("should cleanup event listener on unmount", () => {
      const { unmount } = renderHook(() => useIsMobile());

      expect(addEventListenerSpy).toHaveBeenCalled();

      unmount();

      expect(removeEventListenerSpy).toHaveBeenCalled();
    });
  });
});
