# Chiron
AI powered job search. Use Chiron to find your potential. Named after the mythos figure Chiron who helped many heroes find their potential.

## Features

Chiron provides three core functionalities:

1. **Job Suggestions**: Takes basic information about the user and suggests jobs that are applicable to that person based on skills, experience, location, and preferences.

2. **Email Sorting & Application Tracking**: 
   - Automatically sorts emails related to job applications
   - Grabs responses and logs them into a frontend dashboard
   - Tracks application status: Active (application received), Interested/Needs Attention (follow-up or assessment required), and Closed (application denied)
   - Allows manual entry of applications

3. **AI Cover Letter Generation**: Generates personalized cover letters tailored to each job application using AI.

## Setup

### Prerequisites

- Python 3.8+
- PostgreSQL database
- Gmail API credentials (for email integration)
- OpenAI API key (for cover letter generation)
- Job board API keys (Indeed, Adzuna, etc.)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Chiron
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Create PostgreSQL database:
```bash
createdb chiron_db
```

5. Run the application:
```bash
python src/main.py
```

The application will be available at `http://localhost:8000`

## Configuration

Edit the `.env` file with your configuration:

- `DATABASE_URL`: PostgreSQL connection string
- `GMAIL_CLIENT_ID` and `GMAIL_CLIENT_SECRET`: Gmail API credentials
- `OPENAI_API_KEY`: OpenAI API key for cover letter generation
- `INDEED_API_KEY`, `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`: Job board API keys
- `SECRET_KEY`: Secret key for authentication (change in production)

## Usage

1. **Create User Profile**: Navigate to the Profile section and fill in your information, skills, and upload your resume.

2. **Get Job Suggestions**: Go to the Job Suggestions section to see personalized job recommendations based on your profile.

3. **Track Applications**: 
   - Manually add applications in the Applications section
   - Connect your Gmail account to automatically sync and parse application-related emails
   - View applications organized by status (Active, Interested, Closed)

4. **Generate Cover Letters**: Select an application and generate a personalized cover letter with customizable tone and length.

## API Documentation

Once the server is running, API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
Chiron/
├── src/
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration
│   ├── models/                 # Database models
│   ├── api/                    # API endpoints
│   ├── services/               # Business logic
│   └── database/               # Database setup
├── frontend/                   # Frontend application
│   ├── index.html
│   ├── css/
│   └── js/
├── requirements.txt
└── .env.example
```

## License

MIT License - see LICENSE file for details
