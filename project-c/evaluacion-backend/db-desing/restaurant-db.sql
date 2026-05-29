CREATE SCHEMA IF NOT EXISTS content;

CREATE TABLE content.restaurant (
    id UUID PRIMARY KEY,

    name VARCHAR(120) NOT NULL,
    description TEXT,
    address VARCHAR(255) NOT NULL,

    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE content.table_type (
    id UUID PRIMARY KEY,

    restaurant_id UUID NOT NULL,

    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,

    capacity INT NOT NULL,
    description TEXT,

    price NUMERIC(10,2) NOT NULL,

    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,

    CONSTRAINT chk_table_capacity
        CHECK (capacity > 0),

    CONSTRAINT chk_table_price
        CHECK (price >= 0),
    CONSTRAINT chk_table_type
            CHECK (
                type IN (
                    'shared',
                    'private',
                    'vip',
                    'outdoor',
                    'bar'
                )
            ),
    CONSTRAINT fk_tabletype_restaurant
        FOREIGN KEY (restaurant_id)
        REFERENCES content.restaurant(id)
        ON DELETE CASCADE
);

CREATE TABLE content.menu (
    id UUID PRIMARY KEY,

    restaurant_id UUID NOT NULL,

    name VARCHAR(120) NOT NULL,
    description TEXT,

    courses_count INT NOT NULL,

    active_from DATE NOT NULL,
    active_to DATE NOT NULL,

    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,

    CONSTRAINT chk_courses_count
        CHECK (courses_count > 0),

    CONSTRAINT chk_menu_dates
        CHECK (active_to >= active_from),

    CONSTRAINT fk_menu_restaurant
        FOREIGN KEY (restaurant_id)
        REFERENCES content.restaurant(id)
        ON DELETE CASCADE
);

CREATE TABLE content.menu_item (
    id UUID PRIMARY KEY,

    menu_id UUID NOT NULL,

    name VARCHAR(120) NOT NULL,
    description TEXT,

    course_number INT NOT NULL,

    ingredients TEXT NOT NULL,

    price NUMERIC(10,2) NOT NULL,

    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,

    CONSTRAINT chk_course_number
        CHECK (course_number > 0),

    CONSTRAINT chk_menuitem_price
        CHECK (price >= 0),

    CONSTRAINT fk_menuitem_menu
        FOREIGN KEY (menu_id)
        REFERENCES content.menu(id)
        ON DELETE CASCADE
);

CREATE TABLE content.reservation (
    id UUID PRIMARY KEY,

    restaurant_id UUID NOT NULL,
    table_type_id UUID NOT NULL,

    starts_at TIMESTAMP NOT NULL,
    ends_at TIMESTAMP NOT NULL,

    status VARCHAR(30) NOT NULL,

    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,

    CONSTRAINT chk_reservation_dates
        CHECK (ends_at > starts_at),

    CONSTRAINT chk_reservation_status
        CHECK (
            status IN (
                'pending',
                'confirmed',
                'cancelled',
                'completed'
            )
        ),

    CONSTRAINT uq_table_reservation
        UNIQUE (table_type_id, starts_at),

    CONSTRAINT fk_reservation_restaurant
        FOREIGN KEY (restaurant_id)
        REFERENCES content.restaurant(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_reservation_tabletype
        FOREIGN KEY (table_type_id)
        REFERENCES content.table_type(id)
        ON DELETE RESTRICT
);

CREATE TABLE content.reservation_guest (
    id UUID PRIMARY KEY,

    reservation_id UUID NOT NULL,

    full_name VARCHAR(120) NOT NULL,

    email VARCHAR(255),

    phone VARCHAR(30),

    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,

    CONSTRAINT fk_guest_reservation
        FOREIGN KEY (reservation_id)
        REFERENCES content.reservation(id)
        ON DELETE CASCADE
);


CREATE INDEX idx_reservation_status
ON content.reservation(status);

CREATE INDEX idx_tabletype_restaurant
ON content.table_type(restaurant_id);

CREATE INDEX idx_menuitem_menu
ON content.menu_item(menu_id);

CREATE INDEX idx_guest_reservation
ON content.reservation_guest(reservation_id);





DO $$
DECLARE

    v_restaurant_id UUID := gen_random_uuid();

    v_menu_id UUID := gen_random_uuid();

    v_table_ids UUID[] := ARRAY[]::UUID[];

    v_table_id UUID;

    v_reservation_id UUID;

    v_start_time TIMESTAMP;

    v_guest_count INT;

    v_total_reservations INT := 0;

    i INT;
    j INT;
    k INT;

    v_mesa_idx INT;

    v_dia_offset INT;

    v_allowed_types TEXT[] := ARRAY[
        'shared',
        'private',
        'vip',
        'outdoor',
        'bar'
    ];

    v_statuses TEXT[] := ARRAY[
        'pending',
        'confirmed',
        'completed'
    ];

BEGIN

    -- =====================================================
    -- RESTAURANT
    -- =====================================================

    INSERT INTO content.restaurant (
        id,
        name,
        description,
        address,
        created_at,
        updated_at
    )
    VALUES (
        v_restaurant_id,
        'Mesa Larga Experience',
        'Experiencia gastronómica premium con menú degustación estacional',
        'Av. Gourmet 742, Santa Cruz',
        NOW(),
        NOW()
    );

    -- =====================================================
    -- TABLE TYPES / PHYSICAL TABLES
    -- =====================================================

    FOR i IN 1..15 LOOP

        v_table_id := gen_random_uuid();

        v_table_ids := array_append(v_table_ids, v_table_id);

        INSERT INTO content.table_type (
            id,
            restaurant_id,
            name,
            type,
            capacity,
            description,
            price,
            created_at,
            updated_at
        )
        VALUES (
            v_table_id,
            v_restaurant_id,

            'Mesa ' || i,

            v_allowed_types[((i - 1) % 5) + 1],

            CASE
                WHEN i <= 5 THEN 2
                WHEN i <= 10 THEN 4
                ELSE 6
            END,

            'Mesa premium tipo ' || v_allowed_types[((i - 1) % 5) + 1],

            CASE
                WHEN i <= 5 THEN 45.00
                WHEN i <= 10 THEN 75.00
                ELSE 120.00
            END,

            NOW(),
            NOW()
        );

    END LOOP;

    -- =====================================================
    -- MENU
    -- =====================================================

    INSERT INTO content.menu (
        id,
        restaurant_id,
        name,
        description,
        courses_count,
        active_from,
        active_to,
        created_at,
        updated_at
    )
    VALUES (
        v_menu_id,
        v_restaurant_id,
        'Menú Otoño 2026',
        'Menú degustación inspirado en ingredientes de temporada',
        8,
        CURRENT_DATE,
        CURRENT_DATE + 90,
        NOW(),
        NOW()
    );

    -- =====================================================
    -- MENU ITEMS
    -- =====================================================

    INSERT INTO content.menu_item (
        id,
        menu_id,
        name,
        description,
        course_number,
        ingredients,
        price,
        created_at,
        updated_at
    )
    VALUES

    (
        gen_random_uuid(),
        v_menu_id,
        'Amuse Bouche',
        'Bocado de bienvenida',
        1,
        'Trigo, mantequilla, hierbas',
        12.00,
        NOW(),
        NOW()
    ),

    (
        gen_random_uuid(),
        v_menu_id,
        'Entrada fría',
        'Vegetales frescos y emulsión cítrica',
        2,
        'Lechuga, limón, aceite de oliva',
        18.00,
        NOW(),
        NOW()
    ),

    (
        gen_random_uuid(),
        v_menu_id,
        'Sopa de temporada',
        'Crema suave de vegetales',
        3,
        'Calabaza, zanahoria, crema',
        20.00,
        NOW(),
        NOW()
    ),

    (
        gen_random_uuid(),
        v_menu_id,
        'Pescado blanco',
        'Pescado sellado con reducción cítrica',
        4,
        'Pescado, limón, mantequilla',
        38.00,
        NOW(),
        NOW()
    ),

    (
        gen_random_uuid(),
        v_menu_id,
        'Intermedio',
        'Granizado refrescante',
        5,
        'Menta, limón',
        10.00,
        NOW(),
        NOW()
    ),

    (
        gen_random_uuid(),
        v_menu_id,
        'Carne premium',
        'Corte premium con salsa de vino',
        6,
        'Res, vino tinto',
        55.00,
        NOW(),
        NOW()
    ),

    (
        gen_random_uuid(),
        v_menu_id,
        'Pre-postre',
        'Transición dulce',
        7,
        'Frutas rojas',
        15.00,
        NOW(),
        NOW()
    ),

    (
        gen_random_uuid(),
        v_menu_id,
        'Postre del chef',
        'Postre de chocolate artesanal',
        8,
        'Chocolate, cacao',
        22.00,
        NOW(),
        NOW()
    );

    -- =====================================================
    -- RESERVATIONS
    -- =====================================================

    FOR v_dia_offset IN 0..45 LOOP

        FOR v_mesa_idx IN 1..15 LOOP

            FOR j IN 0..7 LOOP

                EXIT WHEN v_total_reservations >= 450;

                -- 18:00 -> 21:30
                v_start_time :=

                    (
                        CURRENT_DATE
                        + (v_dia_offset || ' days')::interval
                    )

                    + INTERVAL '18 hours'

                    + (j * INTERVAL '30 minutes');

                -- Saltar algunas reservas aleatoriamente
                IF random() < 0.25 THEN
                    CONTINUE;
                END IF;

                v_reservation_id := gen_random_uuid();

                INSERT INTO content.reservation (
                    id,
                    restaurant_id,
                    table_type_id,
                    starts_at,
                    ends_at,
                    status,
                    created_at,
                    updated_at
                )
                VALUES (
                    v_reservation_id,

                    v_restaurant_id,

                    v_table_ids[v_mesa_idx],

                    v_start_time,

                    v_start_time + INTERVAL '30 minutes',

                    v_statuses[(floor(random() * 3)::INT + 1)],

                    NOW(),
                    NOW()
                );

                -- invitados aleatorios
                v_guest_count := floor(random() * 4 + 1);

                FOR k IN 1..v_guest_count LOOP

                    INSERT INTO content.reservation_guest (
                        id,
                        reservation_id,
                        full_name,
                        email,
                        phone,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        gen_random_uuid(),

                        v_reservation_id,

                        'Cliente ' || v_total_reservations || '-' || k,

                        'cliente' || v_total_reservations || k || '@mail.com',

                        '+5917' || lpad((floor(random() * 9999999))::TEXT, 7, '0'),

                        NOW(),
                        NOW()
                    );

                END LOOP;

                v_total_reservations := v_total_reservations + 1;

            END LOOP;

        END LOOP;

    END LOOP;

END $$;