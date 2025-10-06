# Part 4: Database Schema

```mermaid
erDiagram
    users {
        uuid     id PK                    "primary key"
        string   username                 "unique"
        string   email                    "unique"
        string   password_hash
        datetime created_at               "default now"
        boolean  is_verified              "default false"
    }

    profiles {
        uuid     id PK
        uuid     user_id FK               "references users.id; unique to enforce 1:1"
        string   name
        string   campus
        json     contact_info
        string   profile_picture_url
        datetime created_at               "default now"
        datetime updated_at               "auto-updated"
    }

    listings {
        uuid     id PK
        uuid     seller_id FK             "references users.id"
        string   title
        text     description
        decimal  price                    ">= 0"
        string   category
        string   condition                "enum: new | like_new | good | fair"
        string   thumbnail_url
        boolean  is_active                "default true"
        datetime created_at               "default now"
        datetime updated_at               "auto-updated"
    }

    images {
        uuid     id PK
        uuid     listing_id FK            "references listings.id"
        string   url
        boolean  is_thumbnail             "default false"
        string   alt_text
        datetime created_at               "default now"
    }

    admin_actions {
        uuid     id PK
        uuid     admin_id FK              "references users.id (admin performing)"
        uuid     target_user_id FK        "references users.id (target user)"
        uuid     target_listing_id FK     "references listings.id (optional)"
        string   action_type              "enum: warning | strike | ban | listing_removal"
        string   reason
        datetime created_at               "default now"
        datetime expires_at               "optional; null = no expiry"
    }

    %% Relationships
    users     ||--|| profiles       : has_profile
    users     ||--o{ listings       : owns
    listings  ||--o{ images         : has_images
    users     ||--o{ admin_actions  : performs
    users     ||--o{ admin_actions  : is_target
```

**Explanation**: This schema models a marketplace with users, profiles, listings, images, and moderation actions. users holds auth and account flags (unique username/email, is_verified) and has a 1:1 relationship with profiles for personal details. listings belong to a user (seller_id) and capture item metadata (price, category, condition enum), while images attach to listings to store media and optional thumbnail status. admin_actions records moderation events, linking the acting admin (admin_id) and the affected user (target_user_id), and—when relevant—the affected listing via target_listing_id; action_type is an enum (warning/strike/ban/listing_removal), with reason for context and optional expires_at for time-boxed actions. Timestamps (created_at, and updated_at where applicable) support auditing and change tracking.
