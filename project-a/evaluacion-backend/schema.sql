CREATE SCHEMA IF NOT EXISTS content;

CREATE TABLE IF NOT EXISTS content.conference (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(200)  NOT NULL,
    slug        VARCHAR(100)  NOT NULL UNIQUE,
    starts_at   TIMESTAMPTZ   NOT NULL,
    ends_at     TIMESTAMPTZ   NOT NULL,
    timezone    VARCHAR(50)   NOT NULL DEFAULT 'UTC',
    created     TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    modified    TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS content.track (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conference_id   UUID         NOT NULL REFERENCES content.conference(id) ON DELETE CASCADE,
    name            VARCHAR(100) NOT NULL,
    color           VARCHAR(7),
    description     TEXT,
    created         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    modified        TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS content.speaker (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(200) NOT NULL,
    affiliation VARCHAR(200),
    bio         TEXT,
    created     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    modified    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS content.session (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    track_id    UUID         NOT NULL REFERENCES content.track(id) ON DELETE CASCADE,
    title       VARCHAR(300) NOT NULL,
    abstract    TEXT,
    starts_at   TIMESTAMPTZ  NOT NULL,
    ends_at     TIMESTAMPTZ  NOT NULL,
    capacity    INTEGER,
    created     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    modified    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    search_vector TSVECTOR GENERATED ALWAYS AS (
        to_tsvector('english', coalesce(title, '') || ' ' || coalesce(abstract, ''))
    ) STORED
);

CREATE INDEX IF NOT EXISTS idx_session_fts    ON content.session USING GIN(search_vector);
CREATE INDEX IF NOT EXISTS idx_session_starts ON content.session(starts_at);
CREATE INDEX IF NOT EXISTS idx_session_track  ON content.session(track_id);

CREATE TABLE IF NOT EXISTS content.session_speaker (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id  UUID NOT NULL REFERENCES content.session(id)  ON DELETE CASCADE,
    speaker_id  UUID NOT NULL REFERENCES content.speaker(id)  ON DELETE CASCADE,
    created     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    modified    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (session_id, speaker_id)
);

CREATE TABLE IF NOT EXISTS content.registration (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id  UUID         NOT NULL REFERENCES content.session(id) ON DELETE CASCADE,
    user_email  VARCHAR(254) NOT NULL,
    status      VARCHAR(20)  NOT NULL DEFAULT 'confirmed'
                CHECK (status IN ('confirmed', 'waitlist', 'cancelled')),
    created     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    modified    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reg_session_status ON content.registration(session_id, status);
