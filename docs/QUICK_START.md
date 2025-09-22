# Quick Start Guide

## Prerequisites
- Python 3.9+
- Node.js (for frontend assets)
- Docker (optional, for containerized deployment)

## Setup

### 1. Clone the repository
```bash
git clone <repository-url>
cd jarvis
```

### 2. Install dependencies
```bash
# Python dependencies
pip install -r requirements.txt

# Frontend dependencies (if needed)
npm install
```

### 3. Configure environment
Create a `.env` file:
```env
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
```

### 4. Initialize the database
```bash
python init_db.py
```

## Running the Application

### Development Mode
```bash
flask run --debug
```

### Production Mode (with Gunicorn)
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Key Features

### User Onboarding
1. Visit `/onboarding`
2. Complete the initial setup form
3. System generates initial goals

### Quest System
- View daily quests at `/quests`
- Complete quests to earn XP
- Track progress in the dashboard

## Customization

### Adding New Goal Types
1. Update `data/desires_structure.json`
2. Add corresponding quest templates
3. Update the AI prompt templates

### Modifying Styling
- Main styles: `static/css/style.css`
- Uses Tailwind CSS for utility classes
- Custom components in `static/js/components/`

## Troubleshooting

### Common Issues
1. **Missing Dependencies**
   - Run `pip install -r requirements.txt`
   - Check Python version is 3.9+

2. **Database Issues**
   - Delete the database file
   - Run `python init_db.py`

3. **Frontend Not Updating**
   - Clear browser cache
   - Check console for errors
   - Run `npm run build` if using webpack
