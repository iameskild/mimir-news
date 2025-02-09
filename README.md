# Mimir News

> This is an experiment in working with AI agents to interact with prediction markets.

The goal of this project is to build an agentic worklow that pulls market data from prediction markets (currently only [manifold.markets](https://manifold.markets)), filter the markets for ones deemed interested and have solid trading volumes, then perform some research against those markets. Finally, with the research completed, the next step would be to create a video or podcast which discusses the findings in the context of the original prediction market itself.

## Development setup

To get started, you need to install the project dependencies:

```bash
pip install -e .
```

You also need to set the following environment variables.

```bash
cp .env.example .env
```

```bash
OPENAI_API_KEY=<your-openai-api-key>
PERPLEXITY_API_KEY=<your-perplexity-api-key>
```

## Running the project

```bash
crewai run
```

This will output the initial report to the `output.txt` file.

