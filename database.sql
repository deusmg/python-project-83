DROP TABLE IF EXISTS urls CASCADE;
CREATE TABLE urls (
	id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	name VARCHAR(255) UNIQUE NOT NULL,
	created_at TIMESTAMP
);

DROP TABLE IF EXISTS url_checks CASCADE;
CREATE TABLE url_checks (
    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    url_id bigint REFERENCES urls (id),
    status_code integer,
    h1 text,
    title text,
    description text,
    created_at TIMESTAMP
);
