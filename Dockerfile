FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY flask_app.py .

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application using Gunicorn
# Adjust workers based on your server specs (2-4 x num_cores is a good rule of thumb)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "flask_app:app"]