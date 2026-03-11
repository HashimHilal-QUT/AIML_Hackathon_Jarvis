 -- Seed Subscription Tiers
INSERT INTO dim_subscription_tier (tier_id, tier_name, request_limit, price_usd) VALUES
('SILVER', 'Silver', 10000, 29.99),
('BRONZE', 'Bronze', 500000, 99.99),
('GOLD', 'Gold', 1000000, 299.99);

-- Seed User Types
INSERT INTO dim_usertype (user_type_id, user_type_desc) VALUES
('UT01', 'Internal Admin'),
('UT02', 'External User'),
('UT03', 'API Consumer');

-- Seed User Roles
INSERT INTO dim_user_role_type (user_role_id, user_role_desc) VALUES
('UR001', 'Internal User Management'),
('UR002', 'API Management'),
('UR003', 'Basic Access');