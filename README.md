# SafeCall Project

## Setup Instructions

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd safecall
```

### 2. Environment Setup
Create a .env file in the project root:
```bash
cp .env.template .env
```

Edit the .env file and fill in your credentials:
```
SECRET_KEY=your_secure_secret_key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

EMAIL_HOST=your_email_host
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@example.com
EMAIL_HOST_PASSWORD=your_email_password

RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
```

### 3. Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Database Setup
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 5. Static Files
```bash
python manage.py collectstatic
```

### 6. Run the Application
```bash
python manage.py runserver
```

## Deployment Checklist

1. Set DEBUG=False in .env
2. Use a secure SECRET_KEY in .env
3. Configure proper ALLOWED_HOSTS
4. Set up proper email settings
5. Configure your Razorpay credentials (production keys, not test keys)
6. Run `python manage.py check --deploy` to check for deployment issues
7. Set up a proper database (PostgreSQL recommended for production)
8. Configure a web server like Nginx or Apache
9. Set up HTTPS with SSL certificate

## Note on Environment Variables
Never commit your .env file to Git! The .env file contains sensitive information like API keys and passwords. 
