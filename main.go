package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
)

func main() {
	// Cloud Run injects the PORT environment variable.
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080" // Default port if not specified
		log.Printf("Defaulting to port %s", port)
	}

	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		log.Printf("Handling request: %s", r.URL.Path)
		fmt.Fprintln(w, "Hello World from Cloud Run!")
	})

	log.Printf("Listening on port %s", port)
	if err := http.ListenAndServe(":"+port, nil); err != nil {
		log.Fatalf("Error starting server: %s\n", err)
	}
}