# Part 3: Data Models

**User Model**<br>
**Attributes:**

* `id`: UUID, primary key, auto-generated, indexed
* `username`: str, required, unique, indexed — user's display name used in listings and profile
* `email`: str, required, unique, indexed — used for authentication and contact
* `hashed_password`: str, required — hashed version of the user's password (bcrypt via passlib)
* `is_verified`: bool, default `False` — becomes true when user email is verified
* `role`: UserRole enum (`user` | `admin`), default `user`, indexed — determines user permissions
* `created_at`: datetime, default to current timestamp (UTC)

**Relationships:**

* **one to one →** A user has one **profile** (`/api/v1/v1/users/profile` endpoints).
* **one to many →** A user can have many **listings** (`/api/v1/v1/listings` endpoints).
* **one to many →** A user (as admin) can perform many **admin actions** (`admin_actions_performed`).
* **one to many →** A user (as target) can receive many **admin actions** (`admin_actions_received`).

**Explanation:**
This model represents the base registered user in the system — it connects directly to authentication endpoints (`/api/v1/v1/auth/signup`, `/api/v1/v1/auth/login`) and serves as the owner for listings (`/api/v1/v1/listings`) and the associated profile data (`/api/v1/v1/users/profile`). The `role` field enables admin privileges for moderation actions.

---

**Profile Model**<br>
**Attributes:**

* `id`: UUID, primary key, auto-generated
* `user_id`: UUID, foreign key referencing `User.id`, required
* `name`: str, required — full name of the user
* `campus`: str, nullable — name of the user's university or campus
* `contact_info`: dict (JSON), nullable — contains keys like `"email"` and `"phone"`
* `profile_picture_url`: str, nullable — URL of uploaded profile picture
* `created_at`: datetime, default to current timestamp (UTC)
* `updated_at`: datetime, auto-updated on changes (UTC)

**Relationships:**

* **one to one →** Each **profile** belongs to one **user** (linked through unique `user_id`). Cascade delete: profile is deleted when user is deleted.

**Explanation:**
This model corresponds to the `/api/v1/v1/users/profile` endpoints (POST, GET, PATCH, and `/picture` upload). It stores extended personal information that's separate from authentication data, allowing users to manage names, contact info, campus affiliation, and profile images. The unique constraint on `user_id` enforces the one-to-one relationship with User.

---

**Listing Model**<br>
**Attributes:**

* `id`: UUID, primary key, auto-generated
* `seller_id`: UUID, foreign key referencing `User.id`, required
* `title`: str, required — short name of the item being listed
* `description`: str, required — detailed description of the item
* `price`: float, required — must be ≥ 0
* `category`: str, required — e.g., “electronics”, “books”, “furniture”
* `condition`: enum(`new`, `like_new`, `good`, `fair`), required — item condition
* `thumbnail_url`: str, optional — URL to the primary (thumbnail) image
* `is_active`: bool, default `True` — used to hide or deactivate sold listings
* `created_at`: datetime, default to current timestamp
* `updated_at`: datetime, auto-updated on edits

**Relationships:**

* **many to one →** Each **listing** belongs to one **user** (the seller).
* **one to many →** Each **listing** can have multiple **images**.

**Explanation:**
This model powers the `/api/v1/listings` endpoints (GET, POST, PATCH, DELETE) and `/api/v1/users/{user_id}/listings`. It represents an item listed for sale, linking directly to the user who created it and the related images for display.

---

**Image Model**<br>
**Attributes:**

* `id`: UUID, primary key, auto-generated
* `listing_id`: UUID, foreign key referencing `Listing.id`, required
* `url`: str, required — URL where the image file is stored (e.g., CDN or S3 path)
* `is_thumbnail`: bool, default `False` — marks if this image is the listing’s main thumbnail
* `alt_text`: str, optional — descriptive text for accessibility or SEO
* `created_at`: datetime, default to current timestamp

**Relationships:**

* **many to one →** Each **image** belongs to one **listing**.

**Explanation:**
This model supports the `/api/v1/listings/{listing_id}/images` (POST, DELETE) and `/thumbnail` (PATCH) endpoints. It handles image uploads, deletions, and thumbnail assignments, linking media assets directly to their respective listings.

---

**AdminAction Model**<br>
**Attributes:**

* `id`: UUID, primary key, auto-generated
* `admin_id`: UUID, foreign key referencing `User.id`, required — the admin performing the action
* `target_user_id`: UUID, foreign key referencing `User.id`, required — the user being warned, struck, or banned
* `target_listing_id`: UUID, optional — required when action_type = "listing_removal" so you don’t have to infer from the owner
* `action_type`: enum(`warning`, `strike`, `ban`, `listing_removal`), required — defines what moderation action occurred
* `reason`: str, optional — short text explaining why the action was taken
* `created_at`: datetime, default to current timestamp
* `expires_at`: datetime, optional — supports temporary bans; a lift happens automatically when time passes

**Relationships:**

* **many to one →** Each **admin action** is performed by one **admin user**.
* **many to one →** Each **admin action** targets one **user** (the subject of the moderation).

**Explanation:**
Backing the admin moderation and audit log, this model is written by the admin endpoints `/api/v1/admin/actions` and convenience routes for warnings, strikes, bans, and listing removals. Each record captures the acting admin, target user, reason, and timing; `expires_at` enables temporary bans and `target_listing_id` links listing removals to the affected listing.
