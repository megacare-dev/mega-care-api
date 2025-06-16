package main

import (
	"io"
	"log"
	"net/http"
	"os"
)

// main is the entry point of the applications.
func main() {
	// Cloud Run injects the PORT environment variable.
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080" // Default port if not specified
		log.Printf("Defaulting to port %s", port)
	}
	http.HandleFunc("/", helloHandler)
	log.Printf("Listening on port %s", port)
	if err := http.ListenAndServe(":"+port, nil); err != nil {
		log.Fatalf("Error starting server: %s\n", err)
	}
}

// helloHandler handles requests to the root path.
func helloHandler(w http.ResponseWriter, r *http.Request) {
	log.Printf("Handling request: %s", r.URL.Path)
	io.WriteString(w, "Hello World from Cloud Run!\n")
}
