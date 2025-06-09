from crewai import Agent, Crew, Task, Process, TaskOutput
from crewai.project import CrewBase, agent, task, crew
from dotenv import load_dotenv, find_dotenv
from langchain_community.utilities import GoogleSerperAPIWrapper
from crewai.tools import BaseTool
from pydantic import Field

load_dotenv(find_dotenv())

def _print_output(self, output: TaskOutput):
    """Callback function to print the task output to stdout."""
    print("----- Reporting Task Output -----")
    print(output.raw)
    print("---------------------------------")

class SearchTool(BaseTool):
    name: str = "Search"
    description: str = "Find current information about trending ai topics, and developments."
    search: GoogleSerperAPIWrapper = Field(default_factory=GoogleSerperAPIWrapper)

    def _run(self, query: str) -> str:
        try:
            return self.search.run(query)
        except Exception as e:
            return f"Error performing search: {str(e)}"

@CrewBase
class LinkedInTopicCreator:

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def topic_generator_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['topic_generator_agent'], # type: ignore[index]
            tools=[SearchTool()],
            verbose=True
        )

    @task
    def topic_generator_tasks(self) -> Task:
        return Task(
            config=self.tasks_config['topic_generator_tasks'],
            # callback=_print_output
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,  # Automatically collected by the @agent decorator
            tasks=self.tasks,    # Automatically collected by the @task decorator.
            process=Process.sequential,
            verbose=True,
        )

def run_crew():
    result = LinkedInTopicCreator().crew().kickoff()
    print(f"{result}")

if __name__ == "__main__":
    run_crew()