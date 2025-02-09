from crewai import Agent, Task, Crew

from mimir_news.preprocess import get_prediction_market_inputs, call_perplexity_api

markets = get_prediction_market_inputs()

first_market = markets[0]
initial_report = call_perplexity_api(first_market)


goal = """
Your job is to edit the report for clarity and accuracy, and make it more engaging.
The report will be read aloud by a voice assistant, so make sure it's easy to understand.
"""

backstory = """
You are a senior copy editor with a keen eye for detail and a knack for improving the readability of complex information.
You have a deep understanding of the prediction market and the underlying technology.
"""

copy_editor = Agent(
    role="Senior Copy Editor",
    goal=goal,
    backstory=backstory,
)

task_description = f"""
Edit the research report for clarity and accuracy, and make it more engaging.
The report will be read aloud by a voice assistant, so make sure it's easy to understand.

The market question is: {first_market.question}
The probability of the question being answered as True is: {first_market.probability}

The initial report is:
---
{initial_report}
"""

task_goal = """
Deliver a polished research report that is easy to understand and engaging.
Please make sure to include the following information:
- The prediction market name
- The current probability of the prediction market
"""

task = Task(
    agent=copy_editor,
    description=task_description,
    expected_output=task_goal,
    output_file="output.txt",
    verbose=True,
)


mimir_news_crew = Crew(
    agents=[copy_editor],
    tasks=[task],
)
