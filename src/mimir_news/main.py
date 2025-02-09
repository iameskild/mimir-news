import sys
import warnings

from mimir_news.crew import mimir_news_crew

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def run():
    """
    Run the crew.
    """
    try:
        mimir_news_crew.kickoff()
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """

    try:
        mimir_news_crew.train(n_iterations=int(sys.argv[1]), filename=sys.argv[2])

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        mimir_news_crew.replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """

    try:
        mimir_news_crew.test(n_iterations=int(sys.argv[1]), openai_model_name=sys.argv[2])

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")
