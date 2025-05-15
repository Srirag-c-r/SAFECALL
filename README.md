# SafeCall - Crime Reporting System

SafeCall is a comprehensive crime reporting platform built with Django, allowing citizens to report crimes anonymously and track their complaints.

## Deployment Guide

### Prerequisites
- Python 3.11+
- Database (PostgreSQL recommended for production)
- Static file hosting capability

### Local Development Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/safecall.git
   cd safecall
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run migrations:
   ```
   python manage.py migrate
   ```

5. Collect static files:
   ```
   python manage.py collectstatic
   ```

6. Run the development server:
   ```
   python manage.py runserver
   ```

### Deployment on Render.com

1. Push your code to GitHub

2. Create a new Web Service on Render
   - Connect your GitHub repository
   - Select the Python environment
   - Set the build command:
     ```
     pip install -r requirements.txt && python manage.py collectstatic --no-input && python setup_database.py
     ```
   - Set the start command:
     ```
     gunicorn safecall.wsgi:application
     ```

3. Add environment variables:
   - `SECRET_KEY`: Generate a secure random string
   - `DEBUG`: Set to "false" for production
   - `ALLOWED_HOSTS`: Add your domain (e.g., "safecall.onrender.com")
   - `STATIC_URL`: "/static/"
   - `STATIC_ROOT`: "/opt/render/project/src/staticfiles"
   - `WHITENOISE_ALLOW_ALL_ORIGINS`: "true"
   - For API features, add:
     - `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` for payments
     - `NEWSAPI_KEY` for news integration
     - `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` for email

## Troubleshooting

### 500 Server Errors

If you encounter 500 errors after deployment:

1. Check your Render.com logs for specific error messages
2. Verify environment variables are set correctly
3. Run the diagnostic script locally with your production settings:
   ```
   python check_static.py
   ```

### Static Files Not Loading

If videos, images or other static files don't appear on your deployed site:

1. Make sure static files exist in the correct location:
   ```
   python manage.py collectstatic --no-input
   ```

2. Check if `staticfiles` directory has all required files:
   - Verify that key files like `LOGOS/papereffect.mp4` and `LOGOS/gpttlogo.png` are present
   - Run the diagnostic script:
     ```
     python check_static.py
     ```

3. If specific files are missing, manually copy them:
   ```
   cp static/LOGOS/* staticfiles/LOGOS/
   ```

4. Verify WhiteNoise configuration in settings.py:
   - `WHITENOISE_MIMETYPES` should include all your media types
   - `WHITENOISE_ALLOW_ALL_ORIGINS` should be set to True

5. Use the debug endpoints:
   - `/api-config-check/?debug_key=SafeCallDebug123` to check API configuration
   - `/file-check/` to check specific files
   - `/check-video/papereffect.mp4/` to check video files

### API Configuration Issues

If you're experiencing issues with the payment or news features:

1. Make sure all required API keys are set in the environment variables
2. Check the status using `/api-config-check/?debug_key=SafeCallDebug123`
3. For local testing, create a .env file with your API keys:
   ```
   RAZORPAY_KEY_ID=your_key
   RAZORPAY_KEY_SECRET=your_secret
   NEWSAPI_KEY=your_key
   ```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
