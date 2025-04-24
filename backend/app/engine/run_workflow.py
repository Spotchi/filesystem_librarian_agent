import asyncio

from llama_index.core.workflow.events import InputRequiredEvent, HumanResponseEvent
from app.engine.file_workflow import FileAssistantWorkflow

import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))
import llama_index.core
llama_index.core.set_global_handler("simple")


async def main():
    workflow = FileAssistantWorkflow(timeout=300)
    handler = workflow.run()

    async for event in handler.stream_events():
        print(type(event))
        if isinstance(event, InputRequiredEvent):
            print('Asking for input')
            # here, we can handle human input however you want
            # this means using input(), websockets, accessing async state, etc.
            # here, we just use input()
            response = input(event.prefix)
            handler.ctx.send_event(HumanResponseEvent(response=response), 'determine_step')

    print('Done')

if __name__ == "__main__":
    asyncio.run(main())