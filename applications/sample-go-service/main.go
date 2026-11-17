package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
	"time"
)

type HealthResponse struct {
	Status    string    `json:"status"`
	Service   string    `json:"service"`
	GoVersion string    `json:"go_version"`
	Timestamp time.Time `json:"timestamp"`
	UptimeSec float64   `json:"uptime_sec"`
}

type StatusResponse struct {
	Service     string            `json:"service"`
	Environment string            `json:"environment"`
	Port        string            `json:"port"`
	Headers     map[string]string `json:"headers,omitempty"`
}

var startTime = time.Now()

func healthHandler(w http.ResponseWriter, r *http.Request) {
	resp := HealthResponse{
		Status:    "UP",
		Service:   "sample-go-service",
		GoVersion: "1.27.3",
		Timestamp: time.Now().UTC(),
		UptimeSec: time.Since(startTime).Seconds(),
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(resp)
}

func statusHandler(w http.ResponseWriter, r *http.Request) {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	env := os.Getenv("ENVIRONMENT")
	if env == "" {
		env = "local"
	}

	resp := StatusResponse{
		Service:     "sample-go-service",
		Environment: env,
		Port:        port,
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(resp)
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/health", healthHandler)
	mux.HandleFunc("/actuator/health", healthHandler)
	mux.HandleFunc("/api/status", statusHandler)

	server := &http.Server{
		Addr:         ":" + port,
		Handler:      mux,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
	}

	log.Printf("[sample-go-service] Listening on port %s (Go 1.27.3 / Distroless)...", port)
	if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Fatalf("[sample-go-service] Server terminated with error: %v", err)
	}
}
