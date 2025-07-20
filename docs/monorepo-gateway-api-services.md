# Monorepo Strategy: Managing API Gateway and Backend Service

This document outlines the strategy for managing both the primary backend API (`mega-care-api`) and its corresponding API Gateway (Google Cloud Endpoints on Cloud Run) within a single Git repository (a "monorepo").

## 1. Rationale

Using a monorepo for these two tightly-coupled services provides several advantages:

*   **Centralized Management**: All related code lives in one place, simplifying navigation and providing a holistic view of the system.
*   **Atomic Commits**: Changes to the gateway configuration and the backend API can be committed and deployed together, ensuring they are always in sync.
*   **Simplified CI/CD**: A single Cloud Build pipeline can be configured to build, test, and deploy both services, streamlining the deployment process.
*   **Code & Configuration Sharing**: Easier to share configurations, scripts, or documentation between the services.

## 2. Implementation Steps

To implement this, we will restructure the repository and update the CI/CD pipeline.

### Step 1: Adjust Repository Structure

The current structure will be modified to house each service in its own dedicated directory. This separation is crucial for the build process to distinguish between the services.

**New Recommended Structure:**

```
/
├── backend-api/          # Contains the main FastAPI application
│   ├── app/
│   ├── tests/
│   ├── Dockerfile        # Dockerfile specific to the backend API
│   └── requirements.txt
├── api-gateway/          # New directory for the API Gateway
│   ├── openapi.yaml      # Cloud Endpoints configuration
│   └── Dockerfile        # Dockerfile for the ESPv2 gateway proxy
└── cloudbuild.yaml       # Root CI/CD pipeline configuration
```

**Action Required:**
1.  Create a new directory named `backend-api`.
2.  Move the existing `app`, `tests`, `Dockerfile`, `requirements.txt`, and other Python-related files into `backend-api/`.
3.  Create a new directory named `api-gateway`.

### Step 2: Create API Gateway Files

Inside the new `api-gateway/` directory, create the necessary configuration and Docker files.

**a. Gateway Configuration (`api-gateway/openapi.yaml`)**

This file defines the public-facing routes of your API and maps them to the private backend service. It also configures security, such as Firebase JWT validation.

```yaml
# api-gateway/openapi.yaml
swagger: "2.0"
info:
  title: "MegaCare Connect Gateway"
  description: "API Gateway for the MegaCare Connect application"
  version: "1.0.0"
# IMPORTANT: Replace with the URL of your *gateway* Cloud Run service
host: "mega-care-gateway-xxxx.a.run.app"
schemes:
  - "https"
produces:
  - "application/json"

# This section defines the backend service the gateway will forward requests to.
x-google-backend:
  # IMPORTANT: Replace with the URL of your *backend* Cloud Run service
  address: "https://mega-care-api-xxxx.a.run.app"
  # Use http/2 for efficient communication between Cloud Run services
  protocol: "h2"

# Define security schemes. Here, we use Firebase.
securityDefinitions:
  firebase:
    authorizationUrl: ""
    flow: "implicit"
    type: "oauth2"
    # IMPORTANT: Replace 'mega-care-dev' with your GCP Project ID
    x-google-issuer: "https://securetoken.google.com/mega-care-dev"
    x-google-jwks_uri: "https://www.googleapis.com/service_accounts/v1/jwk/securetoken@system.gserviceaccount.com"
    x-google-audiences: "mega-care-dev"

# Define the public paths.
paths:
  # For any path that requires authentication, add the 'security' block.
  /api/v1/customers/me:
    get:
      summary: "Get my profile"
      operationId: "getMyProfile"
      security:
        - firebase: []
      responses:
        '200':
          description: "Successful operation"

  # Public paths like health checks or login do not need the 'security' block.
  /api/v1/auth/line:
    post:
      summary: "LINE Login"
      operationId: "lineLogin"
      responses:
        '200':
          description: "Successful operation"

  # Add all other paths you want to expose through the gateway...
```

**b. Gateway Dockerfile (`api-gateway/Dockerfile`)**

This simple Dockerfile uses Google's pre-built ESPv2 proxy image and injects your `openapi.yaml` configuration.

```dockerfile
# api-gateway/Dockerfile
# Use Google's official serverless Endpoints runtime image
FROM gcr.io/endpoints-runtime-serverless/endpoints-runtime-serverless:2

# Copy the OpenAPI specification into the image at the required location
COPY ./openapi.yaml /etc/endpoints/
```

### Step 3: Update the CI/CD Pipeline (`cloudbuild.yaml`)

The main `cloudbuild.yaml` file at the root of the repository needs to be updated to build and deploy both services. The new pipeline will:
1.  Build the backend image.
2.  Build the gateway image.
3.  Push both images to Artifact Registry.
4.  Deploy the backend service with `ingress` set to `internal-and-cloud-load-balancing` for security.
5.  Deploy the public-facing gateway service.

*For the complete `cloudbuild.yaml` code, please refer to the previous conversation or the final committed file.*

## 4. Summary of Actions

1.  **Restructure:** Create `backend-api` and `api-gateway` directories and move/create files accordingly.
2.  **Configure:** Edit `api-gateway/openapi.yaml` with your specific service URLs and project ID.
3.  **Update Pipeline:** Replace the content of your root `cloudbuild.yaml` with the new version that builds and deploys both services.
4.  **Permissions:** Ensure the Cloud Build service account (`[PROJECT_NUMBER]@cloudbuild.gserviceaccount.com`) has the "Cloud Run Admin" (`roles/run.admin`) and "Service Account User" (`roles/iam.serviceAccountUser`) roles.
5.  **Commit & Push:** Commit all changes to your repository to trigger the new build pipeline.

This setup provides a robust and scalable foundation for managing your services.