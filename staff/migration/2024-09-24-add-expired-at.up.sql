
-- new table
CREATE TABLE user_new (
    id INTEGER PRIMARY KEY,
    name TEXT,
    password_hash TEXT,
    token TEXT,
    notes TEXT,
    type TEXT,
    expired_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- insert data
INSERT INTO user_new (id, name, password_hash, token, notes, type, expired_at)
SELECT id, name, password_hash, token, notes, type, expired_at
FROM user;

-- rename table
DROP TABLE user;
ALTER TABLE user_new RENAME TO user;