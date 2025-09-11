# Deployment Guide

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Open browser to `http://localhost:5000`

## Production Deployment

### Option 1: Heroku

1. Create a Heroku account and install Heroku CLI

2. Initialize git repository:
```bash
git init
git add .
git commit -m "Initial commit"
```

3. Create Heroku app:
```bash
heroku create your-app-name
```

4. Set buildpack for Python:
```bash
heroku buildpacks:set heroku/python
```

5. Deploy:
```bash
git push heroku main
```

6. Open the app:
```bash
heroku open
```

### Option 2: Railway

1. Go to [Railway.app](https://railway.app)
2. Connect your GitHub repository
3. Railway will automatically detect Python and deploy
4. Set environment variables if needed

### Option 3: DigitalOcean App Platform

1. Go to DigitalOcean App Platform
2. Create a new app from GitHub
3. Configure as Python app
4. Deploy

### Option 4: AWS/GCP/Azure

For cloud platforms, use their App Engine/Elastic Beanstalk equivalents with similar Python configuration.

## Environment Variables

Set these for production:

- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 5000)
- `DEBUG`: Debug mode (default: False)

## Performance Notes

- First request may take 15-30 seconds for model loading
- Subsequent requests: 3-10 seconds
- Cached requests: < 1 second
- Memory usage: ~2-4GB RAM recommended
- CPU: Multi-core recommended for parallel processing

## Troubleshooting

- If models fail to load, check available RAM
- For large PDFs, ensure sufficient memory
- Check logs for detailed error messages