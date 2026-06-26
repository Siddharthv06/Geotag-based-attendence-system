-- =====================================================
-- SUPABASE SQL SCHEMA
-- Run this in Supabase Dashboard > SQL Editor
-- =====================================================

-- Users table
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  phone VARCHAR(50),
  role VARCHAR(20) DEFAULT 'member' CHECK (role IN ('admin', 'manager', 'member')),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Sites table
CREATE TABLE sites (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  latitude DOUBLE PRECISION,
  longitude DOUBLE PRECISION,
  radius_meters INTEGER DEFAULT 15,
  address TEXT,
  created_by UUID REFERENCES users(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Site members (many-to-many)
CREATE TABLE site_members (
  site_id UUID REFERENCES sites(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  assigned_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (site_id, user_id)
);

-- Indexes for faster queries
CREATE INDEX idx_sites_created_by ON sites(created_by);
CREATE INDEX idx_site_members_site ON site_members(site_id);
CREATE INDEX idx_site_members_user ON site_members(user_id);

-- Enable Row Level Security (optional - disable for testing)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE sites ENABLE ROW LEVEL SECURITY;
ALTER TABLE site_members ENABLE ROW LEVEL SECURITY;

-- Permissive policies (allow all for development)
CREATE POLICY "Allow all for development" ON users FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for development" ON sites FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for development" ON site_members FOR ALL USING (true) WITH CHECK (true);

-- =====================================================
-- SEED DATA (optional - for testing)
-- =====================================================
INSERT INTO users (name, email, phone, role) VALUES
  ('John Doe', 'john@example.com', '+1234567890', 'admin'),
  ('Jane Smith', 'jane@example.com', '+0987654321', 'manager'),
  ('Bob Wilson', 'bob@example.com', '+1122334455', 'member'),
  ('Alice Brown', 'alice@example.com', '+5566778899', 'member'),
  ('Charlie Davis', 'charlie@example.com', '+9988776655', 'member')
ON CONFLICT (email) DO NOTHING;
