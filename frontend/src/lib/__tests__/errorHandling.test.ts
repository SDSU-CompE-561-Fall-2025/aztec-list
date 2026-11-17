/**
 * Unit tests for errorHandling.ts
 */

import { toast } from "sonner";
import { handleBannedUser, isBannedError, showErrorToast } from "../errorHandling";
import { AUTH_SESSION_ENDED_EVENT, type AuthSessionEndedDetail } from "../auth";

jest.mock("sonner", () => ({
  toast: { error: jest.fn() },
}));

const BANNED_MESSAGE = "Account banned. Contact support for assistance.";

describe("errorHandling.ts", () => {
  let sessionEnded: jest.Mock;
  const onSessionEnded = (event: Event) =>
    sessionEnded((event as CustomEvent<AuthSessionEndedDetail>).detail);

  beforeEach(() => {
    jest.useFakeTimers();
    jest.clearAllMocks();
    localStorage.setItem("auth_token", "test-token");
    localStorage.setItem("user", JSON.stringify({ id: "123" }));
    sessionEnded = jest.fn();
    window.addEventListener(AUTH_SESSION_ENDED_EVENT, onSessionEnded);
  });

  afterEach(() => {
    window.removeEventListener(AUTH_SESSION_ENDED_EVENT, onSessionEnded);
    jest.useRealTimers();
    localStorage.clear();
  });

  describe("isBannedError", () => {
    it("matches the backend's banned message", () => {
      expect(isBannedError(BANNED_MESSAGE)).toBe(true);
      expect(isBannedError("Not found")).toBe(false);
    });
  });

  describe("handleBannedUser", () => {
    it("clears auth and toasts immediately, then ends the session to /login", () => {
      handleBannedUser();

      expect(localStorage.getItem("auth_token")).toBeNull();
      expect(localStorage.getItem("user")).toBeNull();
      expect(toast.error).toHaveBeenCalledWith(
        "Your account has been banned. Contact support for assistance.",
        expect.objectContaining({ duration: 5000 }),
      );
      expect(sessionEnded).not.toHaveBeenCalled();

      jest.advanceTimersByTime(1000);

      expect(sessionEnded).toHaveBeenCalledWith({ redirectTo: "/login" });
    });
  });

  describe("showErrorToast", () => {
    it("routes banned errors to the banned handler", () => {
      showErrorToast(new Error(BANNED_MESSAGE));
      jest.advanceTimersByTime(1000);

      expect(sessionEnded).toHaveBeenCalledWith({ redirectTo: "/login" });
    });

    it("shows other errors without ending the session", () => {
      showErrorToast(new Error("Something broke"));
      jest.advanceTimersByTime(1000);

      expect(toast.error).toHaveBeenCalledWith("Something broke", expect.any(Object));
      expect(sessionEnded).not.toHaveBeenCalled();
      expect(localStorage.getItem("auth_token")).toBe("test-token");
    });
  });
});
