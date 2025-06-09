import warnings

# Suppress all Pydantic UserWarnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.tasks.task_output import TaskOutput
from crewai_tools import DallETool

@CrewBase
class ImageGeneratorCrew:
    """CrewaiDeploymentExample crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def image_generator_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['image_generator_agent'], # type: ignore[index]
            tools=[DallETool(description="Create an engaging image that would be used for ai post and conforms to LinkedIn optimal dimensions")],
            verbose=True
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def image_generator_task(self) -> Task:
        return Task(
            config=self.tasks_config['image_generator_task'],  # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=False,
        )

    def _print_output(self, output: TaskOutput):
        """Callback function to print the task output to stdout."""
        print("----- Reporting Task Output -----")
        print(output.raw)
        print("---------------------------------")
