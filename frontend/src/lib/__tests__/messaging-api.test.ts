/**
 * Unit tests for the report-message and block-user API helpers.
 */

import { reportMessage, blockUser, unblockUser, listMyBlocks } from "../messaging-api";
import { setAuthToken } from "../auth";
import { mockFetch, mockFetchError, cleanupMocks } from "@/test-utils";

describe("messaging report/block api helpers", () => {
  beforeEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
  });

  afterEach(() => {
    cleanupMocks();
  });

  describe("reportMessage", () => {
    it("posts the category and detail to the report endpoint", async () => {
      setAuthToken("test-token");
      mockFetch({ id: "r1", category: "spam", status: "open", created_at: "now" });

      await reportMessage("m1", "spam", "buy now scam");

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/messages/m1/report"),
        expect.objectContaining({
          method: "POST",
          headers: expect.objectContaining({ Authorization: "Bearer test-token" }),
          body: JSON.stringify({ category: "spam", reason_text: "buy now scam" }),
        }),
      );
    });

    it("sends null detail when none is provided", async () => {
      setAuthToken("test-token");
      mockFetch({ id: "r1" });

      await reportMessage("m1", "harassment");

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/messages/m1/report"),
        expect.objectContaining({
          body: JSON.stringify({ category: "harassment", reason_text: null }),
        }),
      );
    });

    it("surfaces the backend detail on error", async () => {
      setAuthToken("test-token");
      mockFetchError("You cannot report your own message.", 400);

      await expect(reportMessage("m1", "spam")).rejects.toThrow(
        "You cannot report your own message.",
      );
    });

    it("throws when not authenticated", async () => {
      await expect(reportMessage("m1", "spam")).rejects.toThrow("Authentication required");
    });
  });

  describe("blockUser / unblockUser", () => {
    it("blockUser POSTs to the block endpoint", async () => {
      setAuthToken("test-token");
      mockFetch({ blocked_user_id: "u2", blocked_username: null, created_at: "now" });

      await blockUser("u2");

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/users/u2/block"),
        expect.objectContaining({ method: "POST" }),
      );
    });

    it("unblockUser DELETEs the block endpoint", async () => {
      setAuthToken("test-token");
      mockFetch({});

      await unblockUser("u2");

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/users/u2/block"),
        expect.objectContaining({ method: "DELETE" }),
      );
    });

    it("blockUser surfaces the backend detail on error", async () => {
      setAuthToken("test-token");
      mockFetchError("Administrators cannot be blocked.", 403);

      await expect(blockUser("admin")).rejects.toThrow("Administrators cannot be blocked.");
    });
  });

  describe("listMyBlocks", () => {
    it("returns the items array from the response", async () => {
      setAuthToken("test-token");
      mockFetch({
        items: [{ blocked_user_id: "u2", blocked_username: "bob", created_at: "now" }],
        count: 1,
      });

      const result = await listMyBlocks();

      expect(result).toHaveLength(1);
      expect(result[0].blocked_user_id).toBe("u2");
    });

    it("throws when not authenticated", async () => {
      await expect(listMyBlocks()).rejects.toThrow("Authentication required");
    });
  });
});
