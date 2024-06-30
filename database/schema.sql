CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL,
  guild_id TEXT NOT NULL,
  message TEXT NOT NULL,
  response TEXT,
  created_at TEXT,
  model_info TEXT,
  object_info TEXT,
  completion_tokens INTEGER,
  prompt_tokens INTEGER,
  total_tokens INTEGER,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
