package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"strings"
	"time"
)

const (
	defaultPort      = "8082"
	defaultJSONLPath = "/data/lifecycle/events.jsonl"
	defaultDBPath    = "/data/lifecycle/lifecycle.duckdb"
	importInterval   = 5 * time.Second
)

func main() {
	healthcheck := flag.Bool("healthcheck", false, "Run healthcheck and exit")
	port := flag.String("port", envOrDefault("PORT", defaultPort), "HTTP server port")
	jsonlPath := flag.String("jsonl", envOrDefault("JSONL_PATH", defaultJSONLPath), "Path to events.jsonl")
	dbPath := flag.String("db", envOrDefault("DB_PATH", defaultDBPath), "Path to DuckDB database file")
	flag.Parse()

	if *healthcheck {
		resp, err := http.Get(fmt.Sprintf("http://localhost:%s/health", *port))
		if err != nil || resp.StatusCode != http.StatusOK {
			os.Exit(1)
		}
		os.Exit(0)
	}

	db, err := NewDB(*dbPath)
	if err != nil {
		log.Fatalf("Failed to open database: %v", err)
	}
	defer db.Close()

	stop := make(chan struct{})
	defer close(stop)
	db.StartImporter(*jsonlPath, importInterval, stop)

	mux := http.NewServeMux()
	mux.HandleFunc("GET /health", handleHealth)
	mux.HandleFunc("GET /api/stats", makeHandler(db, handleStats))
	mux.HandleFunc("GET /api/sessions", makeHandler(db, handleSessions))
	mux.HandleFunc("GET /api/skills", makeHandler(db, handleSkills))
	mux.HandleFunc("GET /api/commands", makeHandler(db, handleCommands))
	mux.HandleFunc("GET /api/agents", makeHandler(db, handleAgents))
	mux.HandleFunc("GET /api/models", makeHandler(db, handleModels))
	mux.HandleFunc("GET /api/projects", makeHandler(db, handleProjects))
	mux.HandleFunc("GET /api/timeline", makeHandler(db, handleTimeline))
	mux.HandleFunc("POST /api/query", makeHandler(db, handleQuery))

	addr := ":" + *port
	log.Printf("Starting duckdb-api on %s (jsonl=%s, db=%s)", addr, *jsonlPath, *dbPath)
	if err := http.ListenAndServe(addr, withCORS(mux)); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}

func envOrDefault(key, defaultVal string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return defaultVal
}

type dbHandler func(db *DB, w http.ResponseWriter, r *http.Request)

func makeHandler(db *DB, fn dbHandler) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		fn(db, w, r)
	}
}

func withCORS(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusOK)
			return
		}
		next.ServeHTTP(w, r)
	})
}

func writeJSON(w http.ResponseWriter, data any) {
	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(data); err != nil {
		log.Printf("ERROR: json encode: %v", err)
	}
}

func writeError(w http.ResponseWriter, code int, msg string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	json.NewEncoder(w).Encode(map[string]string{"error": msg})
}

func handleHealth(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, map[string]string{"status": "ok"})
}

// sessionFilter returns a SQL WHERE clause and args for optional session_id filtering.
func sessionFilter(r *http.Request) (clause string, args []any) {
	sid := r.URL.Query().Get("session_id")
	if sid != "" {
		return " AND session_id = ?", []any{sid}
	}
	return "", nil
}

func handleStats(db *DB, w http.ResponseWriter, r *http.Request) {
	clause, args := sessionFilter(r)
	rows, err := db.Query(`
		SELECT
			COUNT(DISTINCT CASE WHEN event_type = 'session_start' THEN session_id END) AS total_sessions,
			COUNT(CASE WHEN event_type = 'skill_invoke' THEN 1 END) AS total_skill_invocations,
			COUNT(CASE WHEN event_type IN ('agent_start', 'agent_invoke') THEN 1 END) AS total_agent_spawns,
			COUNT(CASE WHEN event_type = 'user_prompt' AND detected_command IS NOT NULL THEN 1 END) AS total_command_invocations,
			COUNT(DISTINCT CASE WHEN event_type = 'skill_invoke' THEN skill_name END) AS unique_skills,
			COUNT(DISTINCT CASE WHEN event_type IN ('agent_start', 'agent_invoke') THEN agent_type END) AS unique_agent_types
		FROM lifecycle_events
		WHERE 1=1`+clause,
		args...)
	if err != nil {
		writeError(w, http.StatusInternalServerError, err.Error())
		return
	}
	if len(rows) > 0 {
		writeJSON(w, rows[0])
	} else {
		writeJSON(w, map[string]any{})
	}
}

func handleSessions(db *DB, w http.ResponseWriter, r *http.Request) {
	groupBy := r.URL.Query().Get("group_by")

	if groupBy == "day" {
		rows, err := db.Query(`
			SELECT
				CAST(event_timestamp AS DATE) AS date,
				COUNT(DISTINCT session_id) AS session_count
			FROM lifecycle_events
			WHERE event_type = 'session_start'
			GROUP BY CAST(event_timestamp AS DATE)
			ORDER BY date
		`)
		if err != nil {
			writeError(w, http.StatusInternalServerError, err.Error())
			return
		}
		writeJSON(w, rows)
		return
	}

	rows, err := db.Query(`
		WITH session_starts AS (
			SELECT session_id, event_timestamp AS started_at, model, cwd, source
			FROM lifecycle_events WHERE event_type = 'session_start'
		),
		session_ends AS (
			SELECT session_id, event_timestamp AS ended_at
			FROM lifecycle_events WHERE event_type = 'session_end'
		),
		session_skills AS (
			SELECT session_id, COUNT(*) AS skill_count
			FROM lifecycle_events WHERE event_type = 'skill_invoke'
			GROUP BY session_id
		),
		session_agents AS (
			SELECT session_id, COUNT(*) AS agent_count
			FROM lifecycle_events WHERE event_type IN ('agent_start', 'agent_invoke')
			GROUP BY session_id
		),
		session_commands AS (
			SELECT session_id, COUNT(*) AS command_count
			FROM lifecycle_events WHERE event_type = 'user_prompt' AND detected_command IS NOT NULL
			GROUP BY session_id
		),
		session_prompts AS (
			SELECT session_id, COUNT(*) AS prompt_count
			FROM lifecycle_events WHERE event_type = 'user_prompt'
			GROUP BY session_id
		)
		SELECT
			s.session_id,
			s.started_at,
			e.ended_at,
			s.model,
			s.source,
			COALESCE(p.prompt_count, 0) AS prompt_count,
			COALESCE(sk.skill_count, 0) AS skill_count,
			COALESCE(a.agent_count, 0) AS agent_count,
			COALESCE(c.command_count, 0) AS command_count
		FROM session_starts s
		LEFT JOIN session_ends e ON s.session_id = e.session_id
		LEFT JOIN session_skills sk ON s.session_id = sk.session_id
		LEFT JOIN session_agents a ON s.session_id = a.session_id
		LEFT JOIN session_commands c ON s.session_id = c.session_id
		LEFT JOIN session_prompts p ON s.session_id = p.session_id
		ORDER BY s.started_at DESC
		LIMIT 100
	`)
	if err != nil {
		writeError(w, http.StatusInternalServerError, err.Error())
		return
	}
	writeJSON(w, rows)
}

func handleSkills(db *DB, w http.ResponseWriter, r *http.Request) {
	groupBy := r.URL.Query().Get("group_by")
	clause, args := sessionFilter(r)

	if groupBy == "day" {
		rows, err := db.Query(`
			SELECT
				CAST(event_timestamp AS DATE) AS date,
				COUNT(*) AS invocation_count
			FROM lifecycle_events
			WHERE event_type = 'skill_invoke'`+clause+`
			GROUP BY CAST(event_timestamp AS DATE)
			ORDER BY date
		`, args...)
		if err != nil {
			writeError(w, http.StatusInternalServerError, err.Error())
			return
		}
		writeJSON(w, rows)
		return
	}

	rows, err := db.Query(`
		SELECT
			skill_name,
			COUNT(*) AS invocation_count,
			COUNT(DISTINCT session_id) AS session_count,
			MIN(event_timestamp) AS first_used,
			MAX(event_timestamp) AS last_used
		FROM lifecycle_events
		WHERE event_type = 'skill_invoke' AND skill_name IS NOT NULL`+clause+`
		GROUP BY skill_name
		ORDER BY invocation_count DESC
	`, args...)
	if err != nil {
		writeError(w, http.StatusInternalServerError, err.Error())
		return
	}
	writeJSON(w, rows)
}

func handleCommands(db *DB, w http.ResponseWriter, r *http.Request) {
	groupBy := r.URL.Query().Get("group_by")
	clause, args := sessionFilter(r)

	if groupBy == "day" {
		rows, err := db.Query(`
			SELECT
				CAST(event_timestamp AS DATE) AS date,
				COUNT(*) AS invocation_count
			FROM lifecycle_events
			WHERE event_type = 'user_prompt' AND detected_command IS NOT NULL`+clause+`
			GROUP BY CAST(event_timestamp AS DATE)
			ORDER BY date
		`, args...)
		if err != nil {
			writeError(w, http.StatusInternalServerError, err.Error())
			return
		}
		writeJSON(w, rows)
		return
	}

	rows, err := db.Query(`
		SELECT
			detected_command AS command_name,
			COUNT(*) AS invocation_count,
			COUNT(DISTINCT session_id) AS session_count
		FROM lifecycle_events
		WHERE event_type = 'user_prompt' AND detected_command IS NOT NULL`+clause+`
		GROUP BY detected_command
		ORDER BY invocation_count DESC
	`, args...)
	if err != nil {
		writeError(w, http.StatusInternalServerError, err.Error())
		return
	}
	writeJSON(w, rows)
}

func handleAgents(db *DB, w http.ResponseWriter, r *http.Request) {
	groupBy := r.URL.Query().Get("group_by")
	clause, args := sessionFilter(r)

	if groupBy == "day" {
		rows, err := db.Query(`
			SELECT
				CAST(event_timestamp AS DATE) AS date,
				COUNT(*) AS spawn_count
			FROM lifecycle_events
			WHERE event_type IN ('agent_start', 'agent_invoke')`+clause+`
			GROUP BY CAST(event_timestamp AS DATE)
			ORDER BY date
		`, args...)
		if err != nil {
			writeError(w, http.StatusInternalServerError, err.Error())
			return
		}
		writeJSON(w, rows)
		return
	}

	rows, err := db.Query(`
		SELECT
			agent_type,
			COUNT(*) AS spawn_count,
			COUNT(DISTINCT session_id) AS session_count
		FROM lifecycle_events
		WHERE event_type IN ('agent_start', 'agent_invoke') AND agent_type IS NOT NULL`+clause+`
		GROUP BY agent_type
		ORDER BY spawn_count DESC
	`, args...)
	if err != nil {
		writeError(w, http.StatusInternalServerError, err.Error())
		return
	}
	writeJSON(w, rows)
}

func handleModels(db *DB, w http.ResponseWriter, r *http.Request) {
	rows, err := db.Query(`
		SELECT
			model,
			COUNT(*) AS session_count,
			MIN(event_timestamp) AS first_seen,
			MAX(event_timestamp) AS last_seen
		FROM lifecycle_events
		WHERE event_type = 'session_start' AND model IS NOT NULL
		GROUP BY model
		ORDER BY session_count DESC
	`)
	if err != nil {
		writeError(w, http.StatusInternalServerError, err.Error())
		return
	}
	writeJSON(w, rows)
}

func handleProjects(db *DB, w http.ResponseWriter, r *http.Request) {
	rows, err := db.Query(`
		WITH session_cwds AS (
			SELECT session_id, cwd
			FROM lifecycle_events
			WHERE event_type = 'session_start' AND cwd IS NOT NULL
		)
		SELECT
			sc.cwd AS project_path,
			COUNT(DISTINCT sc.session_id) AS session_count,
			COALESCE(SUM(CASE WHEN e.event_type = 'skill_invoke' THEN 1 ELSE 0 END), 0) AS skill_count,
			COALESCE(SUM(CASE WHEN e.event_type IN ('agent_start', 'agent_invoke') THEN 1 ELSE 0 END), 0) AS agent_count
		FROM session_cwds sc
		LEFT JOIN lifecycle_events e ON sc.session_id = e.session_id
		GROUP BY sc.cwd
		ORDER BY session_count DESC
	`)
	if err != nil {
		writeError(w, http.StatusInternalServerError, err.Error())
		return
	}
	writeJSON(w, rows)
}

func handleTimeline(db *DB, w http.ResponseWriter, r *http.Request) {
	sessionID := r.URL.Query().Get("session_id")
	if sessionID == "" {
		writeError(w, http.StatusBadRequest, "session_id query parameter is required")
		return
	}

	rows, err := db.Query(`
		SELECT
			event_type,
			event_timestamp,
			session_id,
			COALESCE(skill_name, detected_command, agent_type, source, '') AS detail,
			COALESCE(skill_args, agent_prompt, prompt_text, last_message, '') AS extra
		FROM lifecycle_events
		WHERE session_id = ?
		ORDER BY event_timestamp ASC
	`, sessionID)
	if err != nil {
		writeError(w, http.StatusInternalServerError, err.Error())
		return
	}
	writeJSON(w, rows)
}

func handleQuery(db *DB, w http.ResponseWriter, r *http.Request) {
	var req struct {
		SQL string `json:"sql"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	// Only allow SELECT queries for safety
	trimmed := strings.TrimSpace(strings.ToUpper(req.SQL))
	if !strings.HasPrefix(trimmed, "SELECT") && !strings.HasPrefix(trimmed, "WITH") {
		writeError(w, http.StatusForbidden, "only SELECT queries are allowed")
		return
	}

	rows, err := db.Query(req.SQL)
	if err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}
	writeJSON(w, rows)
}
