package main

import (
	"bufio"
	"database/sql"
	"embed"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"os"
	"sync"
	"time"

	_ "github.com/marcboeker/go-duckdb"
)

//go:embed schema.sql
var schemaFS embed.FS

// LifecycleEvent represents a single lifecycle event from JSONL.
type LifecycleEvent struct {
	EventType       string  `json:"event_type"`
	EventTimestamp  string  `json:"event_timestamp"`
	SessionID       string  `json:"session_id"`
	Source          *string `json:"source"`
	Model           *string `json:"model"`
	Cwd             *string `json:"cwd"`
	PromptText      *string `json:"prompt_text"`
	DetectedCommand *string `json:"detected_command"`
	SkillName       *string `json:"skill_name"`
	SkillArgs       *string `json:"skill_args"`
	AgentID         *string `json:"agent_id"`
	AgentType       *string `json:"agent_type"`
	SubagentModel   *string `json:"subagent_model"`
	AgentPrompt     *string `json:"agent_prompt"`
	TranscriptPath  *string `json:"transcript_path"`
	LastMessage     *string `json:"last_message"`
}

// DB wraps DuckDB connection with import state.
type DB struct {
	conn   *sql.DB
	mu     sync.RWMutex
	offset int64 // byte offset into JSONL file
}

// NewDB opens a DuckDB database and initializes the schema.
func NewDB(dbPath string) (*DB, error) {
	conn, err := sql.Open("duckdb", dbPath)
	if err != nil {
		return nil, fmt.Errorf("open duckdb: %w", err)
	}

	schemaSQL, err := schemaFS.ReadFile("schema.sql")
	if err != nil {
		return nil, fmt.Errorf("read schema: %w", err)
	}

	if _, err := conn.Exec(string(schemaSQL)); err != nil {
		return nil, fmt.Errorf("exec schema: %w", err)
	}

	// Create import state table to persist byte offset across restarts
	if _, err := conn.Exec(`
		CREATE TABLE IF NOT EXISTS import_state (
			key VARCHAR PRIMARY KEY,
			value BIGINT NOT NULL
		)
	`); err != nil {
		return nil, fmt.Errorf("create import_state: %w", err)
	}

	db := &DB{conn: conn}

	// Restore offset from previous run
	var offset int64
	row := conn.QueryRow("SELECT value FROM import_state WHERE key = 'jsonl_offset'")
	if err := row.Scan(&offset); err == nil {
		db.offset = offset
		log.Printf("INFO: restored import offset: %d", offset)
	}

	return db, nil
}

// Close closes the database connection.
func (db *DB) Close() error {
	return db.conn.Close()
}

// Query executes a read-only query and returns results as a slice of maps.
func (db *DB) Query(query string, args ...any) ([]map[string]any, error) {
	db.mu.RLock()
	defer db.mu.RUnlock()

	rows, err := db.conn.Query(query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	columns, err := rows.Columns()
	if err != nil {
		return nil, err
	}

	var results []map[string]any
	for rows.Next() {
		values := make([]any, len(columns))
		valuePtrs := make([]any, len(columns))
		for i := range values {
			valuePtrs[i] = &values[i]
		}

		if err := rows.Scan(valuePtrs...); err != nil {
			return nil, err
		}

		row := make(map[string]any, len(columns))
		for i, col := range columns {
			val := values[i]
			// Convert time.Time to string for JSON serialization
			if t, ok := val.(time.Time); ok {
				row[col] = t.Format(time.RFC3339)
			} else {
				row[col] = val
			}
		}
		results = append(results, row)
	}

	if results == nil {
		results = []map[string]any{}
	}
	return results, rows.Err()
}

// ImportNewEvents reads new lines from the JSONL file and inserts them.
func (db *DB) ImportNewEvents(jsonlPath string) error {
	f, err := os.Open(jsonlPath)
	if err != nil {
		if os.IsNotExist(err) {
			return nil // file doesn't exist yet
		}
		return fmt.Errorf("open jsonl: %w", err)
	}
	defer f.Close()

	info, err := f.Stat()
	if err != nil {
		return fmt.Errorf("stat jsonl: %w", err)
	}

	if info.Size() <= db.offset {
		return nil // no new data
	}

	if _, err := f.Seek(db.offset, io.SeekStart); err != nil {
		return fmt.Errorf("seek jsonl: %w", err)
	}

	var events []LifecycleEvent
	scanner := bufio.NewScanner(f)
	scanner.Buffer(make([]byte, 0, 64*1024), 1024*1024)
	for scanner.Scan() {
		line := scanner.Bytes()
		if len(line) == 0 {
			continue
		}
		var ev LifecycleEvent
		if err := json.Unmarshal(line, &ev); err != nil {
			log.Printf("WARN: skip malformed JSONL line: %v", err)
			continue
		}
		events = append(events, ev)
	}
	if err := scanner.Err(); err != nil {
		return fmt.Errorf("scan jsonl: %w", err)
	}

	newOffset, err := f.Seek(0, io.SeekCurrent)
	if err != nil {
		return fmt.Errorf("tell jsonl: %w", err)
	}

	if len(events) == 0 {
		db.offset = newOffset
		return nil
	}

	db.mu.Lock()
	defer db.mu.Unlock()

	tx, err := db.conn.Begin()
	if err != nil {
		return fmt.Errorf("begin tx: %w", err)
	}
	defer tx.Rollback()

	stmt, err := tx.Prepare(`
		INSERT INTO lifecycle_events (
			event_type, event_timestamp, session_id,
			source, model, cwd,
			prompt_text, detected_command,
			skill_name, skill_args,
			agent_id, agent_type, subagent_model, agent_prompt,
			transcript_path, last_message
		) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
	`)
	if err != nil {
		return fmt.Errorf("prepare stmt: %w", err)
	}
	defer stmt.Close()

	for _, ev := range events {
		ts, err := time.Parse(time.RFC3339, ev.EventTimestamp)
		if err != nil {
			// Try alternative format without timezone
			ts, err = time.Parse("2006-01-02T15:04:05Z", ev.EventTimestamp)
			if err != nil {
				log.Printf("WARN: skip event with bad timestamp: %v", err)
				continue
			}
		}
		_, err = stmt.Exec(
			ev.EventType, ts, ev.SessionID,
			ev.Source, ev.Model, ev.Cwd,
			ev.PromptText, ev.DetectedCommand,
			ev.SkillName, ev.SkillArgs,
			ev.AgentID, ev.AgentType, ev.SubagentModel, ev.AgentPrompt,
			ev.TranscriptPath, ev.LastMessage,
		)
		if err != nil {
			log.Printf("WARN: skip event insert: %v", err)
			continue
		}
	}

	if err := tx.Commit(); err != nil {
		return fmt.Errorf("commit tx: %w", err)
	}

	prevOffset := db.offset
	db.offset = newOffset

	// Persist offset to DuckDB for restart recovery
	if _, err := db.conn.Exec(`
		INSERT INTO import_state (key, value) VALUES ('jsonl_offset', ?)
		ON CONFLICT (key) DO UPDATE SET value = ?
	`, newOffset, newOffset); err != nil {
		log.Printf("WARN: failed to persist offset: %v", err)
	}

	log.Printf("INFO: imported %d events (offset: %d -> %d)", len(events), prevOffset, newOffset)
	return nil
}

// StartImporter runs a background goroutine that imports new events periodically.
func (db *DB) StartImporter(jsonlPath string, interval time.Duration, stop <-chan struct{}) {
	go func() {
		ticker := time.NewTicker(interval)
		defer ticker.Stop()

		// Import once on startup
		if err := db.ImportNewEvents(jsonlPath); err != nil {
			log.Printf("ERROR: initial import: %v", err)
		}

		for {
			select {
			case <-ticker.C:
				if err := db.ImportNewEvents(jsonlPath); err != nil {
					log.Printf("ERROR: import: %v", err)
				}
			case <-stop:
				return
			}
		}
	}()
}
