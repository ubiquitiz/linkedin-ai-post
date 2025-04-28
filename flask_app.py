# app.py
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.job import Job
import pytz
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

mongodb_password = 'Factorial1!'
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Enable CORS
CORS(app)

# MongoDB Configuration
MONGODB_URL = f"mongodb+srv://ubiquitiz:{mongodb_password}@cluster0.d9vqzen.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DATABASE_NAME = os.getenv("DATABASE_NAME", "linkedin_posts")
POST_COLLECTION = "posts"
SCHEDULED_POST_COLLECTION = "scheduled_posts"

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
    """Get scheduled posts collection"""
    db = get_database()
    return db[SCHEDULED_POST_COLLECTION]


# Scheduler Setup
scheduler = BackgroundScheduler()
scheduler.start()

# Define background job for posting to LinkedIn
current_job_id = None


def post_to_linkedin(post_content: str):
    """
    Function to post content to LinkedIn
    This is a placeholder - implement actual LinkedIn API calls here
    """
    # Actual LinkedIn posting logic would go here
    print(f"Posting to LinkedIn at {datetime.now()}: {post_content}")

    # Store the post in the database
    post_collection = get_post_collection()
    post_data = {
        "content": post_content,
        "posted_at": datetime.now(),
        "status": "success"
    }
    post_id = post_collection.insert_one(post_data).inserted_id

    return str(post_id)


# Schedule posts to run at 9:00 AM on Mon, Wed, Fri
def schedule_linkedin_posts():
    global current_job_id

    # Check if there's already a scheduled job
    if current_job_id:
        job = scheduler.get_job(current_job_id)
        if job:
            return current_job_id

    # Get next content to post from the scheduled collection
    scheduled_post = get_next_scheduled_post()
    content = scheduled_post.get("content", "Default LinkedIn post content")

    # Schedule the job
    job = scheduler.add_job(
        post_to_linkedin,
        trigger=CronTrigger(day_of_week="mon,wed,fri", hour=9, minute=0),
        # args=[content],
        name="Generate LinkedIn post",
        id=str(uuid.uuid4()),
        replace_existing=True
    )

    current_job_id = job.id

    # Store job information in database
    schedule_collection = get_scheduled_collection()
    schedule_collection.insert_one({
        "job_id": job.id,
        "content": content,
        "created_at": datetime.now(),
        "next_run": get_next_run_time(job)
    })

    return job.id


def get_next_scheduled_post():
    """Get the next scheduled post from the database"""
    schedule_collection = get_scheduled_collection()
    # Get the most recently scheduled post that hasn't been posted yet
    post = schedule_collection.find_one(
        {"posted": {"$ne": True}},
        sort=[("created_at", -1)]
    )

    if not post:
        return {"content": "Default LinkedIn post content"}

    return post


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


@app.route('/posts/', methods=['POST'])
def create_post():
    """
    Create a new LinkedIn post - either post immediately or schedule for later
    """
    post_data = request.get_json()
    post_collection = get_post_collection()

    if not post_data or 'content' not in post_data:
        return jsonify({"error": "Missing required field: content"}), 400

    content = post_data.get('content')
    schedule_time = post_data.get('schedule_time')

    if schedule_time:
        # Schedule the post for a specific time
        try:
            schedule_time = datetime.fromisoformat(schedule_time)

            # Create a one-time job
            job = scheduler.add_job(
                post_to_linkedin,
                trigger="date",
                run_date=schedule_time,
                args=[content],
                id=str(uuid.uuid4())
            )

            # Store in database
            post_data = {
                "content": content,
                "scheduled_at": datetime.now(),
                "post_time": schedule_time,
                "job_id": job.id,
                "status": "scheduled"
            }
            post_id = post_collection.insert_one(post_data).inserted_id

            return jsonify({
                "id": str(post_id),
                "content": content,
                "posted_at": datetime.now(),
                "status": f"scheduled for {schedule_time}"
            })
        except ValueError:
            return jsonify({"error": "Invalid datetime format. Use ISO format."}), 400
    else:
        # Post immediately
        post_id = post_to_linkedin(content)

        return jsonify({
            "id": post_id,
            "content": content,
            "posted_at": datetime.now(),
            "status": "pending"
        })


@app.route('/posts/', methods=['GET'])
def get_posts():
    """
    Get all LinkedIn posts from the database
    """
    post_collection = get_post_collection()
    posts = []

    for post in post_collection.find():
        posts.append({
            "id": str(post["_id"]),
            "content": post.get("content", ""),
            "posted_at": post.get("posted_at", datetime.now()),
            "status": post.get("status", "unknown")
        })

    return jsonify(posts)


@app.route('/trigger-post/', methods=['POST'])
def trigger_post_now():
    """
    Manually trigger a LinkedIn post immediately
    """
    post_data = request.get_json()

    if not post_data or 'content' not in post_data:
        return jsonify({"error": "Missing required field: content"}), 400

    content = post_data.get('content')
    post_to_linkedin(content)

    return jsonify({"status": "success", "message": "LinkedIn post has been triggered"})


@app.route('/stop-scheduled-posts/', methods=['POST'])
def stop_scheduled_posts():
    """
    Stop all scheduled LinkedIn posts
    """
    global current_job_id

    if current_job_id:
        job = scheduler.get_job(current_job_id)
        if job:
            scheduler.remove_job(current_job_id)
            current_job_id = None
            return jsonify({"status": "success", "message": "Scheduled posts have been stopped"})

    return jsonify({"status": "info", "message": "No scheduled posts to stop"})


@app.route('/next-post-time/', methods=['GET'])
def get_next_post_time():
    """
    Get the time of the next scheduled LinkedIn post
    """
    global current_job_id

    if current_job_id:
        job = scheduler.get_job(current_job_id)
        if job and job.next_run_time:
            next_run = job.next_run_time
            now = datetime.now(pytz.utc)
            countdown = int((next_run - now).total_seconds())
            return jsonify({
                "next_post_time": next_run.strftime("%Y-%m-%d %H:%M:%S"),
                "countdown_seconds": countdown
            })

    # Calculate next post time if no job is scheduled
    now = datetime.now()
    next_run = calculate_next_post_time(now)
    countdown = int((next_run - now).total_seconds())

    return jsonify({
        "next_post_time": next_run.strftime("%Y-%m-%d %H:%M:%S"),
        "countdown_seconds": countdown
    })


@app.route('/health/', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    try:
        # Test MongoDB connection
        db = get_database()
        db.command("ping")

        return jsonify({
            "status": "healthy",
            "database": "connected",
            "scheduler": "running" if scheduler.running else "stopped"
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500


# Setup shutdown handlers
@app.before_request
def setup_application():
    if not hasattr(app, '_setup_done'):
        print("Starting LinkedIn Post Scheduler...")
        app._setup_done = True
        # schedule_linkedin_posts()


# Flask doesn't have a built-in shutdown hook, but
# we can use atexit for graceful shutdown
import atexit


@atexit.register
def shutdown_scheduler():
    print("Shutting down LinkedIn Post Scheduler...")
    scheduler.shutdown()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)