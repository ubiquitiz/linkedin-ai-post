import os, warnings
from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.job import Job
import uuid
from dotenv import load_dotenv
from ai_agents.linkedin_image_generator.crew import ImageGeneratorCrew
from helpers.linked_post_image_api import upload_image_from_url_to_linkedin, create_linkedin_post_with_image
from helpers.reformat_md_files import convert_md_to_linkedin_format
from ai_agents.linkedin_create_post_flow import LinkedInFlow

# Load environment variables
load_dotenv()
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Enable CORS
CORS(app)

# MongoDB Configuration
MONGO_DB_PASSWORD=os.getenv("MONGO_DB_PASSWORD")
MONGODB_URL = f"mongodb+srv://ubiquitiz:{MONGO_DB_PASSWORD}@cluster0.d9vqzen.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DATABASE_NAME = os.getenv("DATABASE_NAME", "linkedin_posts")
POST_COLLECTION = "posts"
SCHEDULED_POST_COLLECTION = "scheduled_posts"
ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")

# Initialize MongoDB client
client = None

def get_database():
    """Get MongoDB database connection"""
    global client
    if client is None:
        client = MongoClient(MONGODB_URL)
    return client.linkedin_posts


def get_post_collection():
    """Get posts collection"""
    db = get_database()
    collection = db[POST_COLLECTION]

    # Check if the collection is empty
    if collection.count_documents({}) == 0:
        # Insert an empty array if the collection is empty
        collection.insert_one({"posts": []})

    return collection


def get_scheduled_collection():
    """Get a scheduled posts collection"""
    db = get_database()
    return db[SCHEDULED_POST_COLLECTION]


# Scheduler Setup
scheduler = BackgroundScheduler()
scheduler.start()

# Define a background job for posting to LinkedIn
current_job_id = None

def post_to_linkedin():
    """
    Function to post content to LinkedIn using CrewAI for content generation
    """
    try:
        # Generate AI image for the post
        image_url = ImageGeneratorCrew().crew().kickoff()
        print(f"Image URL generated at {datetime.now()}: {image_url}")

        if image_url:
            # Upload image to LinkedIn
            image_upload_response = upload_image_from_url_to_linkedin(image_url)

            # Generate post content using CrewAI
            post_kickoff = LinkedInFlow().kickoff()
            formatted_content = convert_md_to_linkedin_format(post_kickoff)

            # Create LinkedIn post with image
            upload_content_response = create_linkedin_post_with_image(
                formatted_content,
                image_upload_response['asset_id']
            )

            # Store the post in the database
            post_collection = get_post_collection()
            post_data = {
                # "content": formatted_content,
                "posted_at": datetime.now(),
                "status": "success",
                "response": upload_content_response
            }
            post_id = post_collection.insert_one(post_data).inserted_id

            # print(f"Posted to LinkedIn at {datetime.now()}: {formatted_content[:100]}...")
            return str(post_id)
        return None
    except Exception as e:
        print(f"Error posting to LinkedIn: {str(e)}")
        # Log error to database
        post_collection = get_post_collection()
        post_data = {
            "error": str(e),
            "posted_at": datetime.now(),
            "status": "failed"
        }
        post_collection.insert_one(post_data)
        return None

def get_next_run_time(job: Job) -> datetime:
    """Get the next run time for a job"""
    return job.next_run_time


def calculate_next_post_time(now: datetime) -> datetime:
    """Calculate the next posting time (Mon, Wed, or Fri at 9:00 AM)"""
    weekday = now.weekday()

    # Map current weekday to next target day (0=Mon, 2=Wed, 4=Fri)
    target_days = [0, 2, 4]
    next_day = next((d for d in target_days if d > weekday), 7)
    days_to_add = (next_day - weekday) % 7

    next_date = now.date() + timedelta(days=days_to_add)
    next_run = datetime.combine(next_date, datetime.min.time()).replace(hour=9, minute=0)

    if next_run <= now:
        next_run += timedelta(days=7)

    return next_run

# Schedule posts to run at 9:00 AM on Mon, Wed, Fri
def schedule_linkedin_posts():
    global current_job_id

    # Check if there's already a scheduled job
    if current_job_id:
        job = scheduler.get_job(current_job_id)
        if job:
            return current_job_id

    # Schedule the job - no need for content since we'll generate it with CrewAI
    job = scheduler.add_job(
        post_to_linkedin,
        trigger=CronTrigger(day_of_week="mon,wed,fri", hour=9, minute=0),
        name="Generate LinkedIn post",
        id=str(uuid.uuid4()),
        replace_existing=True
    )

    current_job_id = job.id

    # Store job information in a database
    schedule_collection = get_scheduled_collection()
    schedule_collection.insert_one({
        "job_id": job.id,
        "created_at": datetime.now(),
        "next_run": get_next_run_time(job)
    })

    return job.id


@app.route('/trigger-post/', methods=['POST'])
def trigger_post_now():
    """
    Manually trigger a LinkedIn post immediately using CrewAI
    """
    try:
        post_id = post_to_linkedin()

        if post_id:
            return jsonify({
                "status": "success",
                "message": "LinkedIn post has been created",
                "post_id": post_id
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to create LinkedIn post"
            }), 500
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# Setup startup handlers
@app.before_request
def setup_application():
    """Setup application - runs once at startup"""
    try:
        print("Starting LinkedIn Post Scheduler...")
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=DeprecationWarning)
            # Schedule the LinkedIn posts
            job_id = schedule_linkedin_posts()
            print(f"LinkedIn posts scheduled - Job ID: {job_id}")
        return True
    except Exception as e:
        print(f"Error during application setup: {e}")
        return False

# Flask doesn't have a built-in shutdown hook, but
# we can use atexit for graceful shutdown
import atexit


@atexit.register
def shutdown_scheduler():
    print("Shutting down LinkedIn Post Scheduler...")
    scheduler.shutdown()

setup_application()

if __name__ == '__main__':
    # setup_application()
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=8000)