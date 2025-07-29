CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    description TEXT,
    usage TEXT
);

CREATE TABLE topics (
    id INTEGER PRIMARY KEY,
    topic TEXT UNIQUE,
    description TEXT
);

CREATE TABLE topic_products (
    topic_id INTEGER,
    product_id INTEGER,
    step TEXT,
    FOREIGN KEY(topic_id) REFERENCES topics(id),
    FOREIGN KEY(product_id) REFERENCES products(id)
);