# Part 3: Data Models

**User Model**<br>
**Attributes:**

* `id`: UUID, primary key, auto-generated
* `username`: str, required, unique — user’s display name used in listings and profile
* `email`: str, required, unique — used for authentication and contact
* `password_hash`: str, required — hashed version of the user’s password
* `created_at`: datetime, default to current timestamp
* `is_verified`: bool, default `False` — becomes true when user email is verified

**Relationships:**

* **one to many →** A user can have many **listings** (`/api/listings` endpoints).
* **one to one →** A user has one **profile** (`/api/users/profile` endpoints).

**Explanation:**
This model represents the base registered user in the system — it connects directly to authentication endpoints (`/api/auth/signup`, `/api/auth/login`) and serves as the owner for listings (`/api/listings`) and the associated profile data (`/api/users/profile`).

---

**Profile Model**<br>
**Attributes:**

* `id`: UUID, primary key, auto-generated
* `user_id`: UUID, foreign key referencing `User.id`, required
* `name`: str, required — full name of the user
* `campus`: str, optional — name of the user’s university or campus
* `contact_info`: dict, optional — contains keys like `"email"` and `"phone"`
* `profile_picture_url`: str, optional — URL of uploaded profile picture
* `created_at`: datetime, default to current timestamp
* `updated_at`: datetime, auto-updated on changes

**Relationships:**

* **one to one →** Each **profile** belongs to one **user** (linked through `user_id`).
* **one to many →** A **profile** can display multiple **listings** posted by the same user.

**Explanation:**
This model corresponds to the `/api/users/profile` endpoints (POST, GET, PATCH, and `/picture` upload). It stores extended personal information that’s separate from authentication data, allowing users to manage names, contact info, campus affiliation, and profile images.

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
This model powers the `/api/listings` endpoints (GET, POST, PATCH, DELETE) and `/api/users/{user_id}/listings`. It represents an item listed for sale, linking directly to the user who created it and the related images for display.

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
This model supports the `/api/listings/{listing_id}/images` (POST, DELETE) and `/thumbnail` (PATCH) endpoints. It handles image uploads, deletions, and thumbnail assignments, linking media assets directly to their respective listings.

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
Backing the admin moderation and audit log, this model is written by the admin endpoints `/api/admin/actions` and convenience routes for warnings, strikes, bans, and listing removals. Each record captures the acting admin, target user, reason, and timing; `expires_at` enables temporary bans and `target_listing_id` links listing removals to the affected listing.
