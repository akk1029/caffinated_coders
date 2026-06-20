BEGIN;

INSERT INTO ingredient_shelf_life (
    item_name,
    category,
    storage_location,
    item_state,
    shelf_life_min_days,
    shelf_life_max_days,
    source_name,
    source_url,
    source_notes
) VALUES
    (
        'raw eggs in shell',
        'Eggs',
        'Refrigerator',
        'raw in shell',
        21,
        35,
        'FoodSafety.gov Cold Food Storage Chart',
        'https://www.foodsafety.gov/food-safety-charts/cold-food-storage-charts',
        'Refrigerator time listed as 3 to 5 weeks.'
    ),
    (
        'hot dogs',
        'Meat',
        'Refrigerator',
        'opened package',
        7,
        7,
        'FoodSafety.gov Cold Food Storage Chart',
        'https://www.foodsafety.gov/food-safety-charts/cold-food-storage-charts',
        'Refrigerator time listed as 1 week.'
    ),
    (
        'hot dogs',
        'Meat',
        'Refrigerator',
        'unopened package',
        14,
        14,
        'FoodSafety.gov Cold Food Storage Chart',
        'https://www.foodsafety.gov/food-safety-charts/cold-food-storage-charts',
        'Refrigerator time listed as 2 weeks.'
    ),
    (
        'hamburger or ground meat',
        'Meat',
        'Refrigerator',
        'raw',
        1,
        2,
        'FoodSafety.gov Cold Food Storage Chart',
        'https://www.foodsafety.gov/food-safety-charts/cold-food-storage-charts',
        'Covers ground beef, turkey, chicken, poultry, veal, pork, lamb, and mixtures.'
    ),
    (
        'chicken or turkey',
        'Poultry',
        'Refrigerator',
        'whole raw',
        1,
        2,
        'FoodSafety.gov Cold Food Storage Chart',
        'https://www.foodsafety.gov/food-safety-charts/cold-food-storage-charts',
        'Refrigerator time listed as 1 to 2 days.'
    ),
    (
        'cooked meat or poultry leftovers',
        'Leftovers',
        'Refrigerator',
        'cooked',
        3,
        4,
        'FoodSafety.gov Cold Food Storage Chart',
        'https://www.foodsafety.gov/food-safety-charts/cold-food-storage-charts',
        'Refrigerator time listed as 3 to 4 days.'
    ),
    (
        'pizza',
        'Leftovers',
        'Refrigerator',
        'leftover',
        3,
        4,
        'FoodSafety.gov Cold Food Storage Chart',
        'https://www.foodsafety.gov/food-safety-charts/cold-food-storage-charts',
        'Refrigerator time listed as 3 to 4 days.'
    ),
    (
        'rice',
        'Dry pantry',
        'Pantry',
        'dry',
        365,
        730,
        'Demo shelf-life estimate',
        NULL,
        'Demo pantry estimate for local testing. Replace with imported FoodKeeper data for production.'
    ),
    (
        'milk',
        'Dairy',
        'Refrigerator',
        'opened',
        7,
        7,
        'Demo shelf-life estimate',
        NULL,
        'Demo refrigerator estimate for local testing. Replace with imported FoodKeeper data for production.'
    ),
    (
        'spinach',
        'Produce',
        'Refrigerator',
        'fresh',
        3,
        5,
        'Demo shelf-life estimate',
        NULL,
        'Demo refrigerator estimate for local testing. Replace with imported FoodKeeper data for production.'
    ),
    (
        'apples',
        'Produce',
        'Pantry',
        'fresh',
        14,
        21,
        'Demo shelf-life estimate',
        NULL,
        'Demo pantry estimate for local testing. Replace with imported FoodKeeper data for production.'
    )
ON CONFLICT ON CONSTRAINT ingredient_shelf_life_lookup_unique
DO UPDATE SET
    category = EXCLUDED.category,
    shelf_life_min_days = EXCLUDED.shelf_life_min_days,
    shelf_life_max_days = EXCLUDED.shelf_life_max_days,
    source_name = EXCLUDED.source_name,
    source_url = EXCLUDED.source_url,
    source_notes = EXCLUDED.source_notes;

COMMIT;
