-- Create shared database for multi-bot coordination
CREATE DATABASE cartame_shared;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE cartame TO postgres;
GRANT ALL PRIVILEGES ON DATABASE cartame_shared TO postgres;
