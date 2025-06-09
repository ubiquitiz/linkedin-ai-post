from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, crew, task
from config.llm_config import llm

@CrewBase
class LinkedInPostCreator:
    """LinkedIn post creator with optimized single-step processing"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self):
        super().__init__()
        self.topic = None
        self.input_data = {}

    @agent
    def linkedin_post_creator(self) -> Agent:
        return Agent(
            config=self.agents_config['linkedin_post_creator'],
            llm=llm,
            verbose=False  # Reduced verbosity for speed
        )

    @task
    def create_linkedin_post_task(self) -> Task:
        return Task(
            config=self.tasks_config['create_linkedin_post_task'],
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[self.linkedin_post_creator()],
            tasks=[self.create_linkedin_post_task()],
            process=Process.sequential,
            verbose=False,
        )

def run_crew():
    result = LinkedInPostCreator().crew().kickoff()
    print(f"{result}")

if __name__ == "__main__":
    run_crew()