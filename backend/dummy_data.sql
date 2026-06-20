BEGIN;

-- Passwords for both accounts: Password123!
-- Hash generated with passlib bcrypt (cost 12)
INSERT INTO users (
    user_id,
    username,
    email,
    hashed_password,
    recipes_generated_today,
    subscription_tier,
    subscription_expiry,
    total_co2_saved,
    total_money_saved,
    created_at
) VALUES
    (
        '00000000-0000-0000-0000-000000000001',
        'demo_free_user',
        'demo_free@example.com',
        '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
        2,
        'Free',
        NULL,
        4.750,
        0,
        now() - INTERVAL '30 days'
    ),
    (
        '00000000-0000-0000-0000-000000000002',
        'demo_premium_user',
        'demo_premium@example.com',
        '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
        5,
        'Premium',
        now() + INTERVAL '25 days',
        11.200,
        0,
        now() - INTERVAL '90 days'
    )
ON CONFLICT (user_id)
DO UPDATE SET
    username = EXCLUDED.username,
    email = EXCLUDED.email,
    hashed_password = EXCLUDED.hashed_password,
    recipes_generated_today = EXCLUDED.recipes_generated_today,
    subscription_tier = EXCLUDED.subscription_tier,
    subscription_expiry = EXCLUDED.subscription_expiry,
    total_co2_saved = EXCLUDED.total_co2_saved,
    created_at = EXCLUDED.created_at;

-- ingredient_shelf_life data lives in sample_shelf_life_seed.sql — run that first.

INSERT INTO subscriptions_log (
    transaction_id,
    user_id,
    payment_date,
    amount,
    status
) VALUES
    (
        '10000000-0000-0000-0000-000000000001',
        '00000000-0000-0000-0000-000000000002',
        now() - INTERVAL '5 days',
        9.99,
        'Success'
    ),
    (
        '10000000-0000-0000-0000-000000000002',
        '00000000-0000-0000-0000-000000000001',
        now() - INTERVAL '10 days',
        9.99,
        'Failed'
    )
ON CONFLICT (transaction_id)
DO UPDATE SET
    user_id = EXCLUDED.user_id,
    payment_date = EXCLUDED.payment_date,
    amount = EXCLUDED.amount,
    status = EXCLUDED.status;

INSERT INTO digital_pet (
    pet_id,
    user_id,
    health_points,
    mood_status,
    appearance_level,
    experience_points,
    evolution_stage
) VALUES
    (
        '20000000-0000-0000-0000-000000000001',
        '00000000-0000-0000-0000-000000000001',
        82,
        'Curious',
        2,
        135,
        'Baby'
    ),
    (
        '20000000-0000-0000-0000-000000000002',
        '00000000-0000-0000-0000-000000000002',
        96,
        'Happy',
        4,
        390,
        'Teen'
    )
ON CONFLICT (pet_id)
DO UPDATE SET
    user_id = EXCLUDED.user_id,
    health_points = EXCLUDED.health_points,
    mood_status = EXCLUDED.mood_status,
    appearance_level = EXCLUDED.appearance_level,
    experience_points = EXCLUDED.experience_points,
    evolution_stage = EXCLUDED.evolution_stage;

INSERT INTO ingredients_inventory (
    batch_id,
    user_id,
    shelf_life_id,
    item_name,
    quantity,
    unit,
    upload_date,
    expiry_date,
    status,
    estimated_cost
) VALUES
    (
        '30000000-0000-0000-0000-000000000001',
        '00000000-0000-0000-0000-000000000001',
        (SELECT shelf_life_id FROM ingredient_shelf_life WHERE item_name_key = 'raw eggs in shell' AND storage_location = 'Refrigerator' AND item_state_key = 'raw in shell'),
        'raw eggs in shell',
        12,
        'count',
        now() - INTERVAL '20 days',
        NULL,
        'Pantry',
        4.50
    ),
    (
        '30000000-0000-0000-0000-000000000002',
        '00000000-0000-0000-0000-000000000001',
        (SELECT shelf_life_id FROM ingredient_shelf_life WHERE item_name_key = 'hot dogs' AND storage_location = 'Refrigerator' AND item_state_key = 'opened package'),
        'hot dogs',
        1,
        'pack',
        now() - INTERVAL '6 days',
        NULL,
        'Pantry',
        5.99
    ),
    (
        '30000000-0000-0000-0000-000000000003',
        '00000000-0000-0000-0000-000000000001',
        (SELECT shelf_life_id FROM ingredient_shelf_life WHERE item_name_key = 'rice' AND storage_location = 'Pantry' AND item_state_key = 'dry'),
        'rice',
        2,
        'kg',
        now() - INTERVAL '30 days',
        NULL,
        'Pantry',
        7.25
    ),
    (
        '30000000-0000-0000-0000-000000000004',
        '00000000-0000-0000-0000-000000000001',
        (SELECT shelf_life_id FROM ingredient_shelf_life WHERE item_name_key = 'pizza' AND storage_location = 'Refrigerator' AND item_state_key = 'leftover'),
        'pizza',
        2,
        'slices',
        now() - INTERVAL '2 days',
        NULL,
        'Consumed',
        6.00
    ),
    (
        '30000000-0000-0000-0000-000000000005',
        '00000000-0000-0000-0000-000000000002',
        (SELECT shelf_life_id FROM ingredient_shelf_life WHERE item_name_key = 'milk' AND storage_location = 'Refrigerator' AND item_state_key = 'opened'),
        'milk',
        1,
        'liter',
        now() - INTERVAL '5 days',
        NULL,
        'Pantry',
        3.80
    ),
    (
        '30000000-0000-0000-0000-000000000006',
        '00000000-0000-0000-0000-000000000002',
        (SELECT shelf_life_id FROM ingredient_shelf_life WHERE item_name_key = 'spinach' AND storage_location = 'Refrigerator' AND item_state_key = 'fresh'),
        'spinach',
        250,
        'g',
        now() - INTERVAL '3 days',
        NULL,
        'Pantry',
        4.20
    ),
    (
        '30000000-0000-0000-0000-000000000007',
        '00000000-0000-0000-0000-000000000002',
        (SELECT shelf_life_id FROM ingredient_shelf_life WHERE item_name_key = 'apples' AND storage_location = 'Pantry' AND item_state_key = 'fresh'),
        'apples',
        6,
        'count',
        now() - INTERVAL '4 days',
        NULL,
        'Pantry',
        5.40
    ),
    (
        '30000000-0000-0000-0000-000000000008',
        '00000000-0000-0000-0000-000000000002',
        (SELECT shelf_life_id FROM ingredient_shelf_life WHERE item_name_key = 'cooked meat or poultry leftovers' AND storage_location = 'Refrigerator' AND item_state_key = 'cooked'),
        'cooked meat or poultry leftovers',
        1,
        'container',
        now() - INTERVAL '1 day',
        NULL,
        'Consumed',
        9.75
    )
ON CONFLICT (batch_id)
DO UPDATE SET
    user_id = EXCLUDED.user_id,
    shelf_life_id = EXCLUDED.shelf_life_id,
    item_name = EXCLUDED.item_name,
    quantity = EXCLUDED.quantity,
    unit = EXCLUDED.unit,
    upload_date = EXCLUDED.upload_date,
    expiry_date = NULL,
    status = EXCLUDED.status,
    estimated_cost = EXCLUDED.estimated_cost;

SELECT recalculate_user_money_saved('00000000-0000-0000-0000-000000000001');
SELECT recalculate_user_money_saved('00000000-0000-0000-0000-000000000002');

INSERT INTO meals (
    meal_id,
    user_id,
    meal_name,
    estimated_calories,
    meal_date
) VALUES
    (
        '40000000-0000-0000-0000-000000000001',
        '00000000-0000-0000-0000-000000000001',
        'Egg Fried Rice',
        620,
        now() - INTERVAL '1 day'
    ),
    (
        '40000000-0000-0000-0000-000000000002',
        '00000000-0000-0000-0000-000000000002',
        'Spinach Chicken Bowl',
        540,
        now()
    )
ON CONFLICT (meal_id)
DO UPDATE SET
    user_id = EXCLUDED.user_id,
    meal_name = EXCLUDED.meal_name,
    estimated_calories = EXCLUDED.estimated_calories,
    meal_date = EXCLUDED.meal_date;

INSERT INTO meal_images (
    image_id,
    meal_id,
    image_url,
    upload_date,
    ai_processed
) VALUES
    (
        '50000000-0000-0000-0000-000000000001',
        '40000000-0000-0000-0000-000000000001',
        'https://example.com/demo/egg-fried-rice.jpg',
        now() - INTERVAL '1 day',
        true
    ),
    (
        '50000000-0000-0000-0000-000000000002',
        '40000000-0000-0000-0000-000000000002',
        'https://example.com/demo/spinach-chicken-bowl.jpg',
        now(),
        false
    )
ON CONFLICT (image_id)
DO UPDATE SET
    meal_id = EXCLUDED.meal_id,
    image_url = EXCLUDED.image_url,
    upload_date = EXCLUDED.upload_date,
    ai_processed = EXCLUDED.ai_processed;

INSERT INTO recipes (
    recipe_id,
    user_id,
    recipe_title,
    recipe_description,
    generated_date
) VALUES
    (
        '60000000-0000-0000-0000-000000000001',
        '00000000-0000-0000-0000-000000000001',
        'Use-It-Up Egg Rice',
        'A simple rice dish that uses eggs close to their expiry date.',
        now()
    ),
    (
        '60000000-0000-0000-0000-000000000002',
        '00000000-0000-0000-0000-000000000002',
        'Creamy Spinach Pasta',
        'A quick recipe designed to use opened milk and fresh spinach.',
        now()
    )
ON CONFLICT (recipe_id)
DO UPDATE SET
    user_id = EXCLUDED.user_id,
    recipe_title = EXCLUDED.recipe_title,
    recipe_description = EXCLUDED.recipe_description,
    generated_date = EXCLUDED.generated_date;

INSERT INTO recipe_ingredients (
    recipe_ingredient_id,
    recipe_id,
    ingredient_name,
    quantity,
    unit
) VALUES
    (
        '70000000-0000-0000-0000-000000000001',
        '60000000-0000-0000-0000-000000000001',
        'raw eggs in shell',
        2,
        'count'
    ),
    (
        '70000000-0000-0000-0000-000000000002',
        '60000000-0000-0000-0000-000000000001',
        'rice',
        0.25,
        'kg'
    ),
    (
        '70000000-0000-0000-0000-000000000003',
        '60000000-0000-0000-0000-000000000002',
        'spinach',
        120,
        'g'
    ),
    (
        '70000000-0000-0000-0000-000000000004',
        '60000000-0000-0000-0000-000000000002',
        'milk',
        0.2,
        'liter'
    )
ON CONFLICT (recipe_ingredient_id)
DO UPDATE SET
    recipe_id = EXCLUDED.recipe_id,
    ingredient_name = EXCLUDED.ingredient_name,
    quantity = EXCLUDED.quantity,
    unit = EXCLUDED.unit;

INSERT INTO pet_activity_log (
    activity_id,
    pet_id,
    activity_type,
    points_change,
    activity_date
) VALUES
    (
        '80000000-0000-0000-0000-000000000001',
        '20000000-0000-0000-0000-000000000001',
        'Consumed expiring ingredient',
        20,
        now() - INTERVAL '2 days'
    ),
    (
        '80000000-0000-0000-0000-000000000002',
        '20000000-0000-0000-0000-000000000002',
        'Generated recipe',
        10,
        now() - INTERVAL '1 day'
    ),
    (
        '80000000-0000-0000-0000-000000000003',
        '20000000-0000-0000-0000-000000000002',
        'Logged meal image',
        15,
        now()
    )
ON CONFLICT (activity_id)
DO UPDATE SET
    pet_id = EXCLUDED.pet_id,
    activity_type = EXCLUDED.activity_type,
    points_change = EXCLUDED.points_change,
    activity_date = EXCLUDED.activity_date;

COMMIT;
