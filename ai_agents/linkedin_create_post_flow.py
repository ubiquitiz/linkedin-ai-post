from dotenv import load_dotenv, find_dotenv
from crewai.flow.flow import Flow, listen, start
from flask import Flask
from ai_agents.linkedin_topic_creator.topic_creator_crew import LinkedInTopicCreator
from ai_agents.linkedin_create_post.create_post_crew import LinkedInPostCreator

load_dotenv(find_dotenv())
app = Flask(__name__)


class LinkedInFlow(Flow):
    input_variables = {}

    @start()
    def generate_research_topic(self):
        return LinkedInTopicCreator().crew().kickoff()

    @listen(generate_research_topic)
    def create_linkedin_post(self, topic):
        # Extract the actual content from the CrewOutput object
        if hasattr(topic, 'raw'):
            # For newer CrewAI versions that use .raw
            topic_content = topic.raw
        elif hasattr(topic, 'result'):
            # For older CrewAI versions that use .result
            topic_content = topic.result
        else:
            # Fallback to string representation
            topic_content = str(topic)

        self.input_variables['topic'] = topic_content.strip('"')
        print(f"Generated LinkedIn Topic: {self.input_variables}")
        return LinkedInPostCreator().crew().kickoff(self.input_variables).raw

## This is optional,
## but uncomment if you want to run the Flask server locally
# @app.route('/create-post', methods=['POST'])
# def run():
#     try:
#         linkedin_flow = LinkedInFlow()
#         content = linkedin_flow.kickoff()
#         return jsonify({"output": content})
#     except Exception as e:
#         return jsonify({"error": str(e)})
#
# if __name__ == "__main__":
#     app.run(host='0.0.0.0', port=8000)