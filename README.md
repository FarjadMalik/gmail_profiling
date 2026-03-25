# Gmail Email Profiling Tool

This project is a Python-based tool for analyzing a user's Gmail account using the official Google Gmail API. It provides functionalities to authenticate, fetch, and profile emails based on various criteria like labels, senders, and dates.

## Features

-   **Secure Authentication**: Uses OAuth 2.0 to securely connect to your Gmail account.
-   **Email Filtering**: List and retrieve emails filtered by labels, specific senders, and date ranges.
-   **Metadata Extraction**: Efficiently fetch email metadata (like From, Subject, Date) for individual or multiple emails using batch requests.
-   **Content Parsing**: Extract and clean the body content from emails, handling both plain text and HTML parts.
-   **Sender Analysis**:
    -   Identify all unique senders for a given label.
    -   Count emails per day and list the unique senders for that day.
-   **Subscription Identification**: Heuristically identify subscription-based emails from mail headers.

## Project Structure

```
.
├── auth/
│   ├── authentication.py   # Handles Google API authentication.
│   └── credentials.json    # Your Google Cloud API credentials.
├── profiling/
│   ├── analysis.py         # High-level analysis functions.
│   ├── emails.py           # Core class for interacting with emails.
│   └── utils.py            # Helper utilities.
└── main.py                 # Main script to run the profiling workflow.
```

## Setup and Usage

### 1. Prerequisites

-   Python 3.x
-   A Google Cloud Platform project.

### 2. Installation

1.  **Clone the repository:**
    ```sh
    git clone <your-repository-url>
    cd <repository-directory>
    ```

2.  **Set up Google API Credentials:**
    -   Go to the [Google Cloud Console](https://console.cloud.google.com/).
    -   Create a new project.
    -   Enable the **Gmail API** for your project.
    -   Go to "Credentials", click "Create Credentials", and choose "OAuth client ID".
    -   Select "Desktop app" as the application type.
    -   Download the JSON file. Rename it to `credentials.json` and place it inside the `auth/` directory.

3.  **Install Dependencies:**
    It is recommended to use a virtual environment.
    ```sh
    # Create and activate a virtual environment (e.g., venv)
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

    # Install required packages
    pip install google-api-python-client google-auth-oauthlib python-dateutil beautifulsoup4
    ```

### 3. Running the Application

Execute the main script from the root directory:

```sh
python main.py
```

-   On the first run, you will be prompted to authorize the application by logging into your Google account in a web browser.
-   A `token.pickle` file will be created in the `auth/` directory to store your authorization token for future runs.

You can modify [`main.py`](main.py) to customize the analysis, such as changing the target label, sender