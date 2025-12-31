summary: Learn how to secure an A2UI Restaurant Finder agent using Firebase Authentication.
id: restaurant-finder-firebase
categories: a2ui,firebase,security
tags: a2ui,firebase,auth
status: Published
authors: A2UI Team
Feedback Link: https://github.com/google/A2UI/issues

# Building a Secure A2UI Restaurant Finder with Firebase

## Overview
Duration: 0:05

In this codelab, you will learn how to add authentication to an **A2UI (Agent to UI)** application. We will take the existing "Restaurant Finder" sample and secure it using **Firebase Authentication**.

### What you will build
You will modify both the client (Shell) and the server (Agent) to ensure that only authenticated users can access the application and that the agent knows who is making the request.

-   **Client**: A Web Shell built with Lit that forces users to sign in with Google before accessing the agent.
-   **Server**: A Python A2A Agent that verifies the user's identity token on every request.

### Why do we need this?
By default, the samples are open. In a real-world scenario:
1.  **User Identity**: You want to know *who* is asking for restaurant recommendations (maybe to save preferences or history).
2.  **Security**: You don't want unauthorized users calling your LLM backend and consuming your quota.
3.  **Trust**: A2UI renders UI based on agent responses; ensuring the channel is secure is critical.

## Prerequisites
Duration: 0:05

Before starting, ensure you have the following installed:

-   [Node.js](https://nodejs.org/) (v18+)
-   [Python](https://www.python.org/) (v3.13+)
-   [UV](https://docs.astral.sh/uv/) (Python package manager)
-   [Git](https://git-scm.com/)

You also need a Google account to create a Firebase project.

## Step 1: Firebase Setup
Duration: 0:10

First, we need a backend to handle authentication. We'll use Firebase.

1.  Go to the [Firebase Console](https://console.firebase.google.com/).
2.  Click **Add project** and name it `a2ui-restaurant-finder` (or similar).
3.  Disable Google Analytics for this demo (optional) and click **Create project**.
4.  Once created, go to **Authentication** in the left sidebar.
5.  Click **Get started**.
6.  Select **Google** as a Sign-in method.
7.  Enable it, select your support email, and click **Save**.

### Get Client Config
1.  Click the **Gear icon** (Project Settings) > **General**.
2.  Scroll to **Your apps** and click the **</> (Web)** icon.
3.  Register the app (nickname: "Shell").
4.  Copy the `firebaseConfig` object shown. You'll need this for the client.

### Get Server Config
1.  In Project Settings, go to the **Service accounts** tab.
2.  Click **Generate new private key**.
3.  Save the JSON file. This is your "Service Account Key".
4.  Rename it to `service-account.json` and move it to a secure location (don't commit it!).

## Step 2: Configure the Client
Duration: 0:10

Now let's configure the web client (`samples/client/lit/shell`).

### 1. Install Dependencies
Navigate to the shell directory and install `firebase`:

```bash
cd samples/client/lit/shell
npm install firebase
```

### 2. Configure Environment Variables
We use environment variables to keep secrets out of the code.

1.  Create a `.env` file in `samples/client/lit/shell`:
    ```bash
    cp .env.example .env
    ```
2.  Open `.env` and fill in the values from the `firebaseConfig` object you copied earlier:
    ```
    VITE_FIREBASE_API_KEY=AIza...
    VITE_FIREBASE_AUTH_DOMAIN=...
    VITE_FIREBASE_PROJECT_ID=...
    ...
    ```

### 3. Update App Configuration
We've updated `configs/restaurant.ts` to read these values using `import.meta.env`. This allows the application to pick up your configuration at build time.

## Step 3: Implement Client Authentication
Duration: 0:15

We've modified the shell application (`app.ts`) to handle the authentication flow.

### How it works
1.  **Auth Service**: We created an `AuthService` (`auth/auth.ts`) that wraps the Firebase SDK. It handles signing in with Google and retrieving the **ID Token**.
2.  **UI Gate**: In `app.ts`, we check if a user is logged in.
    -   If **No**: We render a "Sign In" button.
    -   If **Yes**: We render the main application (Theme toggle, Input form, etc.).
3.  **Token Passing**: The `A2UIClient` (`client.ts`) now accepts a token provider. Before every request to the server, it fetches the latest valid ID token and attaches it to the `Authorization` header:
    ```typescript
    headers.set("Authorization", `Bearer ${token}`);
    ```

This ensures that the server always receives a valid proof of identity.

## Step 4: Configure the Server
Duration: 0:10

Now let's secure the Python backend (`samples/agent/adk/restaurant_finder`).

### 1. Install Dependencies
The server needs the Firebase Admin SDK to verify tokens.

```bash
cd samples/agent/adk/restaurant_finder
# Add firebase-admin to pyproject.toml
# Then run:
uv sync
```

### 2. Set Credentials
The Admin SDK needs the Service Account Key to authenticate with Firebase servers. Set the environment variable:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
```

## Step 5: Implement Server Verification
Duration: 0:10

We've added a middleware to the server (`__main__.py`) that intercepts every request.

### The Middleware Logic
1.  **Intercept**: The `FirebaseAuthMiddleware` captures incoming HTTP requests.
2.  **Extract**: It looks for the `Authorization: Bearer <token>` header.
3.  **Verify**: It uses `auth.verify_id_token(token)` from the Admin SDK to validate the token's signature and expiration.
4.  **Log**: It extracts the user's email from the token and logs it:
    ```python
    logger.info(f"Request authenticated for user: {email}")
    ```
5.  **Reject**: If the token is missing or invalid, it returns a `401 Unauthorized` error, protecting your agent logic.

## Step 6: Run the Application
Duration: 0:05

Now that everything is configured, let's run it!

### 1. Start the Server
In a terminal, verify credentials are set and start the agent:

```bash
cd samples/agent/adk/restaurant_finder
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
uv run .
```

### 2. Start the Client
In a separate terminal, start the web shell:

```bash
cd samples/client/lit/shell
npm run dev
```

### 3. Test It
1.  Open `http://localhost:5173/?app=restaurant` in your browser.
2.  You should see a **"Sign In with Google"** button. The app is protected!
3.  Click it and sign in with your Google account.
4.  Once signed in, the Restaurant Finder interface appears.
5.  Type "Find me pizza places".
6.  Check the **Server Terminal**. You should see a log entry:
    `INFO:__main__:Request authenticated for user: your.email@gmail.com`

## Conclusion
Duration: 0:05

Congratulations! You have successfully secured your A2UI application.

### What we covered
-   Setting up Firebase Auth for Google Sign-In.
-   Configuring a Vite-based Lit application with environment variables.
-   Passing Bearer tokens from client to server.
-   Verifying tokens in a Python Starlette backend using Middleware.
-   Logging authenticated user actions.

This pattern establishes a secure foundation for building personalized and protected Agentic UI experiences.
