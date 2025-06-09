FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY linkedin_post_app.py .

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application using Gunicorn
# Adjust workers based on your server specs (2-4 x num_cores is a good rule of thumb)
CMD ["gunicorn", "-w", "1", "linkedin_post_app:app"]