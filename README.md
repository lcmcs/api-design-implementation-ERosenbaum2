# Minyan Finder API

A RESTful API for finding nearby people who need a minyan (prayer group). Users can broadcast their location and search for others nearby who need the same type of minyan.

## Features

- **POST /broadcasts** - Create a new broadcast when looking for a minyan
- **GET /broadcasts/nearby** - Find nearby broadcasts within a specified radius
- **PUT /broadcasts/{id}** - Update an existing broadcast
- **DELETE /broadcasts/{id}** - Delete a broadcast
- **Swagger UI** - Interactive API documentation at `/docs`

## Tech Stack

- **Python 3.8+**
- **Flask** - Web framework
- **Flask-RESTX** - API framework with Swagger/OpenAPI support
- **SQLAlchemy** - ORM for database operations
- **PostgreSQL** - Database
- **Render** - Deployment platform

## Project Structure

```
api-design-implementation-ERosenbaum2/
├── app.py                 # Main Flask application
├── models.py              # Database models (SQLAlchemy)
├── routes.py              # API route handlers
├── utils.py               # Helper functions (distance calculation)
├── requirements.txt       # Python dependencies
├── openapi.yaml           # OpenAPI 3.0 specification
├── render.yaml            # Render deployment configuration
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- PostgreSQL database (local or remote)
- pip (Python package manager)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd api-design-implementation-ERosenbaum2
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   
   Create a `.env` file in the root directory:
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/minyan_finder
   FLASK_ENV=development
   PORT=5000
   ```

5. **Create the database**
   
   Make sure PostgreSQL is running and create a database:
   ```sql
   CREATE DATABASE minyan_finder;
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

   The API will be available at `http://localhost:5000`
   Swagger UI will be available at `http://localhost:5000/docs`

## API Endpoints

### 1. Create Broadcast

**POST** `/broadcasts`

Create a new broadcast when looking for a minyan.

**Request Body:**
```json
{
  "latitude": 40.7128,
  "longitude": -74.0060,
  "minyanType": "mincha",
  "earliestTime": "2025-03-26T13:00:00Z",
  "latestTime": "2025-03-26T14:00:00Z"
}
```

**Response (201 Created):**
```json
{
  "id": "abc123-def456-ghi789",
  "message": "Broadcast created successfully"
}
```

### 2. Find Nearby Broadcasts

**GET** `/broadcasts/nearby`

Find broadcasts within a specified radius.

**Query Parameters:**
- `latitude` (required) - Latitude of search location
- `longitude` (required) - Longitude of search location
- `radius` (required) - Search radius in miles
- `minyanType` (optional) - Filter by minyan type (shacharit, mincha, maariv)

**Example:**
```
GET /broadcasts/nearby?latitude=40.7130&longitude=-74.0059&radius=2&minyanType=mincha
```

**Response (200 OK):**
```json
[
  {
    "id": "abc123-def456-ghi789",
    "latitude": 40.7128,
    "longitude": -74.0060,
    "minyanType": "mincha",
    "earliestTime": "2025-03-26T13:00:00Z",
    "latestTime": "2025-03-26T14:00:00Z",
    "active": true,
    "createdAt": "2025-03-26T12:45:00Z"
  }
]
```

### 3. Update Broadcast

**PUT** `/broadcasts/{id}`

Update an existing broadcast. Only provided fields will be updated.

**Request Body:**
```json
{
  "latitude": 40.7140,
  "longitude": -74.0065,
  "latestTime": "2025-03-26T14:30:00Z"
}
```

**Response (200 OK):**
```json
{
  "message": "Broadcast updated successfully"
}
```

### 4. Delete Broadcast

**DELETE** `/broadcasts/{id}`

Delete a broadcast.

**Response (204 No Content):**
No response body

## Deployment to Render

### Prerequisites

- Render account (sign up at https://render.com)
- GitHub repository with your code

### Steps

1. **Push your code to GitHub**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Create a new Web Service on Render**
   - Go to Render dashboard
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Render will detect the `render.yaml` file

3. **Configure Environment Variables**
   - Render will automatically set `DATABASE_URL` from the database service
   - The `render.yaml` file handles this configuration

4. **Deploy**
   - Render will automatically build and deploy your application
   - The build command: `pip install -r requirements.txt`
   - The start command: `python app.py`

5. **Access your API**
   - Your API will be available at: `https://your-app-name.onrender.com`
   - Swagger UI: `https://your-app-name.onrender.com/docs`

### Manual Deployment (Alternative)

If you prefer to set up services manually:

1. **Create PostgreSQL Database**
   - Go to Render dashboard
   - Click "New +" → "PostgreSQL"
   - Name it `minyan-finder-db`
   - Note the connection string

2. **Create Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Set build command: `pip install -r requirements.txt`
   - Set start command: `python app.py`
   - Add environment variable:
     - Key: `DATABASE_URL`
     - Value: (from PostgreSQL service)
   - Add environment variable:
     - Key: `FLASK_ENV`
     - Value: `production`
   - Add environment variable:
     - Key: `PORT`
     - Value: `5000`

## Testing the API

### Using cURL

**Create a broadcast:**
```bash
curl -X POST http://localhost:5000/broadcasts \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 40.7128,
    "longitude": -74.0060,
    "minyanType": "mincha",
    "earliestTime": "2025-03-26T13:00:00Z",
    "latestTime": "2025-03-26T14:00:00Z"
  }'
```

**Find nearby broadcasts:**
```bash
curl "http://localhost:5000/broadcasts/nearby?latitude=40.7130&longitude=-74.0059&radius=2&minyanType=mincha"
```

**Update a broadcast:**
```bash
curl -X PUT http://localhost:5000/broadcasts/{id} \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 40.7140,
    "longitude": -74.0065
  }'
```

**Delete a broadcast:**
```bash
curl -X DELETE http://localhost:5000/broadcasts/{id}
```

### Using Swagger UI

Navigate to `http://localhost:5000/docs` (or your production URL) to use the interactive Swagger UI for testing all endpoints.

## Data Model

### Broadcast

- `id` (UUID) - Unique identifier
- `latitude` (Float) - Latitude coordinate (-90 to 90)
- `longitude` (Float) - Longitude coordinate (-180 to 180)
- `minyanType` (String) - Type of minyan: `shacharit`, `mincha`, or `maariv`
- `earliestTime` (DateTime) - Earliest time for the minyan (ISO 8601 UTC)
- `latestTime` (DateTime) - Latest time for the minyan (ISO 8601 UTC)
- `active` (Boolean) - Whether the broadcast is currently active
- `createdAt` (DateTime) - When the broadcast was created (ISO 8601 UTC)

## Distance Calculation

The API uses the Haversine formula to calculate distances between geographic coordinates. Distances are returned in miles.

## Error Handling

The API returns appropriate HTTP status codes:

- `200 OK` - Successful request
- `201 Created` - Resource created successfully
- `204 No Content` - Resource deleted successfully
- `400 Bad Request` - Invalid input or missing parameters
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

Error responses include a JSON object with an `error` field:
```json
{
  "error": "Error message here"
}
```

## License

This project is created for educational purposes.

## Support

For issues or questions, please open an issue in the GitHub repository.

