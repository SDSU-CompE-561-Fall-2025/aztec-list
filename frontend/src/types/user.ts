/**
 * User and profile type definitions.
 */

export interface UserPublic {
  id: string;
  username: string;
  is_verified: boolean;
  created_at: string;
}

export interface UserPrivate extends UserPublic {
  email: string;
}

export interface ContactInfo {
  email?: string;
  phone?: string;
}

export interface ProfilePublic {
  id: string;
  user_id: string;
  name: string;
  campus: string | null;
  contact_info: ContactInfo | null;
  profile_picture_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface UserWithProfile {
  user: UserPublic;
  profile: ProfilePublic | null;
}
