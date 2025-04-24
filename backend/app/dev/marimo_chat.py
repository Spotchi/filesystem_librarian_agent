

import marimo

__generated_with = "0.13.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(mo):
    def simple_echo_model(messages, config):
        print(messages)
        return f"You said: {messages[-1].content}"

    mo.ui.chat(
        simple_echo_model,
        prompts=["Hello", "How are you?"],
        show_configuration_controls=True
    )
    return


@app.cell
def _():
    from app.engine.get_agent import get_agent

    return (get_agent,)


@app.cell
def _(get_agent):
    from llama_index.core.llms.mock import MockLLM

    mock_llm = MockLLM()
    agent = get_agent(mock_llm, [])
    return (MockLLM,)


@app.cell
async def _(MockLLM):
    from llama_index.core.workflow import (
        Event,
        StartEvent,
        StopEvent,
        Workflow,
        step,
    )

    class JokeEvent(Event):
        joke: str


    class JokeFlow(Workflow):
        llm = MockLLM()

        @step
        async def generate_joke(self, ev: StartEvent) -> JokeEvent:
            topic = ev.topic

            prompt = f"Write your best joke about {topic}."
            response = await self.llm.acomplete(prompt)
            return JokeEvent(joke=str(response))

        @step
        async def critique_joke(self, ev: JokeEvent) -> StopEvent:
            joke = ev.joke

            prompt = f"Give a thorough analysis and critique of the following joke: {joke}"
            response = await self.llm.acomplete(prompt)
            return StopEvent(result=str(response))


    w = JokeFlow(timeout=60, verbose=False)
    result = await w.run(topic="pirates")
    print(str(result))
    return


@app.cell
def _():
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
