from ai_agents.linkedin_image_generator.crew import ImageGeneratorCrew
from flask import Flask, jsonify
import os
from datetime import datetime

app = Flask(__name__)

@app.route('/generate-image', methods=['POST'])
def run():
    """Run the ImageGeneratorCrew and return the result."""
    try:
        # Generate content
        output_dir = "../../output"
        os.makedirs(output_dir, exist_ok=True)  # Ensure the directory exists
        content = ImageGeneratorCrew().crew().kickoff()

        # Save content to a Markdown file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"generate_image_{timestamp}.md"

        with open(os.path.join(output_dir, filename), 'w') as f:
            f.write("# LinkedIn Post Image\n\n")
            f.write(content.raw)
        os.path.join(output_dir, filename)
        print(f"Content saved to {filename}")
        return jsonify({"output": content.raw})
    except Exception as e:
        return jsonify({"error": str(e)})

## This is optional,
## but uncomment if you want to run the Flask server locally
# if __name__ == '__main__':
#   app.run(host='0.0.0.0', port=8080)