BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'subscription_tier_enum') THEN
        CREATE TYPE subscription_tier_enum AS ENUM ('Free', 'Premium');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'payment_status_enum') THEN
        CREATE TYPE payment_status_enum AS ENUM ('Success', 'Failed', 'Refunded');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'inventory_status_enum') THEN
        CREATE TYPE inventory_status_enum AS ENUM ('Pantry', 'Consumed', 'Expired', 'Discarded');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'storage_location_enum') THEN
        CREATE TYPE storage_location_enum AS ENUM ('Pantry', 'Refrigerator', 'Freezer');
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(80) NOT NULL UNIQUE,
    recipes_generated_today INT NOT NULL DEFAULT 0 CHECK (recipes_generated_today >= 0),
    subscription_tier subscription_tier_enum NOT NULL DEFAULT 'Free',
    subscription_expiry TIMESTAMPTZ,
    total_co2_saved NUMERIC(12, 3) NOT NULL DEFAULT 0 CHECK (total_co2_saved >= 0),
    total_money_saved NUMERIC(12, 2) NOT NULL DEFAULT 0 CHECK (total_money_saved >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS email VARCHAR(255) UNIQUE,
    ADD COLUMN IF NOT EXISTS hashed_password TEXT NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS total_co2_saved NUMERIC(12, 3) NOT NULL DEFAULT 0 CHECK (total_co2_saved >= 0),
    ADD COLUMN IF NOT EXISTS total_money_saved NUMERIC(12, 2) NOT NULL DEFAULT 0 CHECK (total_money_saved >= 0),
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now();

CREATE TABLE IF NOT EXISTS ingredient_shelf_life (
    shelf_life_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_name VARCHAR(160) NOT NULL,
    item_name_key TEXT GENERATED ALWAYS AS (lower(btrim(item_name))) STORED,
    category VARCHAR(120),
    storage_location storage_location_enum NOT NULL,
    item_state VARCHAR(80) NOT NULL DEFAULT 'fresh',
    item_state_key TEXT GENERATED ALWAYS AS (lower(btrim(item_state))) STORED,
    shelf_life_min_days INT NOT NULL CHECK (shelf_life_min_days > 0),
    shelf_life_max_days INT NOT NULL CHECK (shelf_life_max_days >= shelf_life_min_days),
    source_name VARCHAR(180) NOT NULL,
    source_url TEXT,
    source_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ingredient_shelf_life_lookup_unique
        UNIQUE (item_name_key, storage_location, item_state_key)
);

CREATE TABLE IF NOT EXISTS subscriptions_log (
    transaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    payment_date TIMESTAMPTZ NOT NULL DEFAULT now(),
    amount NUMERIC(10, 2) NOT NULL CHECK (amount >= 0),
    status payment_status_enum NOT NULL
);

CREATE TABLE IF NOT EXISTS ingredients_inventory (
    batch_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    shelf_life_id UUID REFERENCES ingredient_shelf_life(shelf_life_id) ON DELETE SET NULL,
    item_name VARCHAR(160) NOT NULL,
    quantity NUMERIC(12, 3) NOT NULL CHECK (quantity >= 0),
    unit VARCHAR(40) NOT NULL,
    upload_date TIMESTAMPTZ NOT NULL DEFAULT now(),
    expiry_date TIMESTAMPTZ,
    status inventory_status_enum NOT NULL DEFAULT 'Pantry',
    estimated_cost NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (estimated_cost >= 0),
    storage_location storage_location_enum NOT NULL DEFAULT 'Pantry',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT inventory_expiry_after_upload
        CHECK (expiry_date IS NULL OR expiry_date >= upload_date)
);

ALTER TABLE ingredients_inventory
    ADD COLUMN IF NOT EXISTS estimated_cost NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (estimated_cost >= 0),
    ADD COLUMN IF NOT EXISTS shelf_life_id UUID REFERENCES ingredient_shelf_life(shelf_life_id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS storage_location storage_location_enum NOT NULL DEFAULT 'Pantry',
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now();

CREATE TABLE IF NOT EXISTS digital_pet (
    pet_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
    health_points INT NOT NULL DEFAULT 100 CHECK (health_points >= 0),
    mood_status VARCHAR(80) NOT NULL DEFAULT 'Neutral',
    appearance_level INT NOT NULL DEFAULT 1 CHECK (appearance_level >= 1),
    experience_points INT NOT NULL DEFAULT 0 CHECK (experience_points >= 0),
    evolution_stage VARCHAR(20) NOT NULL DEFAULT 'Egg'
        CHECK (evolution_stage IN ('Egg', 'Baby', 'Teen', 'Adult'))
);

ALTER TABLE digital_pet
    ADD COLUMN IF NOT EXISTS experience_points INT NOT NULL DEFAULT 0 CHECK (experience_points >= 0),
    ADD COLUMN IF NOT EXISTS evolution_stage VARCHAR(20) NOT NULL DEFAULT 'Egg'
        CHECK (evolution_stage IN ('Egg', 'Baby', 'Teen', 'Adult'));

CREATE TABLE IF NOT EXISTS pet_activity_log (
    activity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pet_id UUID NOT NULL REFERENCES digital_pet(pet_id) ON DELETE CASCADE,
    activity_type VARCHAR(120) NOT NULL,
    points_change INT NOT NULL,
    activity_date TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS meals (
    meal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    meal_name VARCHAR(160) NOT NULL,
    estimated_calories NUMERIC(10, 2) CHECK (estimated_calories IS NULL OR estimated_calories >= 0),
    meal_date TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS meal_images (
    image_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meal_id UUID NOT NULL REFERENCES meals(meal_id) ON DELETE CASCADE,
    image_url VARCHAR(2048) NOT NULL,
    upload_date TIMESTAMPTZ NOT NULL DEFAULT now(),
    ai_processed BOOLEAN NOT NULL DEFAULT false
);

CREATE TABLE IF NOT EXISTS recipes (
    recipe_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    recipe_title VARCHAR(180) NOT NULL,
    recipe_description TEXT,
    generated_date TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS recipe_ingredients (
    recipe_ingredient_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipe_id UUID NOT NULL REFERENCES recipes(recipe_id) ON DELETE CASCADE,
    ingredient_name VARCHAR(160) NOT NULL,
    quantity NUMERIC(12, 3) CHECK (quantity IS NULL OR quantity >= 0),
    unit VARCHAR(40)
);

CREATE INDEX IF NOT EXISTS subscriptions_log_user_id_idx
    ON subscriptions_log(user_id);

CREATE INDEX IF NOT EXISTS ingredients_inventory_user_id_idx
    ON ingredients_inventory(user_id);

CREATE INDEX IF NOT EXISTS ingredients_inventory_expiry_date_idx
    ON ingredients_inventory(expiry_date);

CREATE INDEX IF NOT EXISTS ingredients_inventory_status_idx
    ON ingredients_inventory(status);

CREATE INDEX IF NOT EXISTS ingredients_inventory_shelf_life_id_idx
    ON ingredients_inventory(shelf_life_id);

CREATE INDEX IF NOT EXISTS pet_activity_log_pet_id_idx
    ON pet_activity_log(pet_id);

CREATE INDEX IF NOT EXISTS meals_user_id_idx
    ON meals(user_id);

CREATE INDEX IF NOT EXISTS meal_images_meal_id_idx
    ON meal_images(meal_id);

CREATE INDEX IF NOT EXISTS recipes_user_id_idx
    ON recipes(user_id);

CREATE INDEX IF NOT EXISTS recipe_ingredients_recipe_id_idx
    ON recipe_ingredients(recipe_id);

CREATE OR REPLACE FUNCTION set_inventory_expiry_date()
RETURNS TRIGGER AS $$
DECLARE
    selected_days INT;
    selected_storage_location storage_location_enum;
    should_set_expiry BOOLEAN;
BEGIN
    IF NEW.upload_date IS NULL THEN
        NEW.upload_date := now();
    END IF;

    IF NEW.shelf_life_id IS NULL THEN
        RETURN NEW;
    END IF;

    SELECT shelf_life_min_days, storage_location
    INTO selected_days, selected_storage_location
    FROM ingredient_shelf_life
    WHERE shelf_life_id = NEW.shelf_life_id;

    IF selected_days IS NULL THEN
        RETURN NEW;
    END IF;

    NEW.storage_location := selected_storage_location;

    IF TG_OP = 'INSERT' THEN
        should_set_expiry := NEW.expiry_date IS NULL;
    ELSE
        should_set_expiry :=
            NEW.expiry_date IS NULL
            OR (
                NEW.expiry_date IS NOT DISTINCT FROM OLD.expiry_date
                AND (
                    NEW.shelf_life_id IS DISTINCT FROM OLD.shelf_life_id
                    OR NEW.upload_date IS DISTINCT FROM OLD.upload_date
                )
            );
    END IF;

    IF should_set_expiry THEN
        NEW.expiry_date := NEW.upload_date + make_interval(days => selected_days);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_set_inventory_expiry_date ON ingredients_inventory;

CREATE TRIGGER trg_set_inventory_expiry_date
BEFORE INSERT OR UPDATE OF upload_date, expiry_date, shelf_life_id, storage_location
ON ingredients_inventory
FOR EACH ROW
EXECUTE FUNCTION set_inventory_expiry_date();

CREATE OR REPLACE FUNCTION recalculate_user_money_saved(target_user_id UUID)
RETURNS NUMERIC AS $$
DECLARE
    calculated_money NUMERIC(12, 2);
BEGIN
    SELECT COALESCE(SUM(estimated_cost), 0)::NUMERIC(12, 2)
    INTO calculated_money
    FROM ingredients_inventory
    WHERE user_id = target_user_id
      AND status = 'Consumed';

    UPDATE users
    SET total_money_saved = calculated_money
    WHERE user_id = target_user_id;

    RETURN calculated_money;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE VIEW ingredients_inventory_current AS
SELECT
    ii.*,
    CASE
        WHEN ii.status = 'Pantry'
             AND ii.expiry_date IS NOT NULL
             AND ii.expiry_date < now()
        THEN 'Expired'::inventory_status_enum
        ELSE ii.status
    END AS calculated_status
FROM ingredients_inventory ii;

CREATE OR REPLACE VIEW user_dashboard_metrics AS
SELECT
    u.user_id,
    u.username,
    COUNT(ii.batch_id) FILTER (WHERE ii.status = 'Pantry') AS pantry_batches,
    COUNT(ii.batch_id) FILTER (
        WHERE ii.status = 'Pantry'
          AND ii.expiry_date IS NOT NULL
          AND ii.expiry_date <= CURRENT_DATE + INTERVAL '3 days'
    ) AS expiring_soon,
    u.total_co2_saved,
    u.total_money_saved,
    COALESCE(dp.experience_points, 0) AS pet_experience_points,
    COALESCE(dp.evolution_stage, 'Egg') AS pet_evolution_stage,
    CASE
        WHEN dp.pet_id IS NULL THEN 0::NUMERIC
        WHEN dp.evolution_stage = 'Egg' THEN
            LEAST(100::NUMERIC, GREATEST(0::NUMERIC, ROUND(dp.experience_points::NUMERIC / 100 * 100, 2)))
        WHEN dp.evolution_stage = 'Baby' THEN
            LEAST(100::NUMERIC, GREATEST(0::NUMERIC, ROUND((dp.experience_points - 100)::NUMERIC / 150 * 100, 2)))
        WHEN dp.evolution_stage = 'Teen' THEN
            LEAST(100::NUMERIC, GREATEST(0::NUMERIC, ROUND((dp.experience_points - 250)::NUMERIC / 250 * 100, 2)))
        ELSE 100::NUMERIC
    END AS pet_progress_percent,
    u.recipes_generated_today AS recipes_today
FROM users u
LEFT JOIN ingredients_inventory ii
    ON ii.user_id = u.user_id
LEFT JOIN digital_pet dp
    ON dp.user_id = u.user_id
GROUP BY
    u.user_id,
    u.username,
    u.total_co2_saved,
    u.total_money_saved,
    u.recipes_generated_today,
    dp.pet_id,
    dp.experience_points,
    dp.evolution_stage;

COMMIT;
