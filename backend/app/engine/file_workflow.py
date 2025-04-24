from llama_index.core.workflow import InputRequiredEvent, HumanResponseEvent, Workflow, step, StartEvent, StopEvent, Event, Context

from app.engine.workflow_utils import visible_step
from app.engine.determining_steps import StepChoice
from llama_index.core.prompts import PromptTemplate
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.openai import OpenAI

import logging

from backend.app.engine import get_agent

class TreeInputEvent(Event):
    pass


class AgentInit(Event):
    pass


# User input events
class RequestedOperations(Event):
    pass

class UnclearUserRequest(Event):
    pass

class UserGivenConfirmation(Event):
    pass


class OperationSuggestion(Event):
    pass

class UserConfirmationReceived(Event):
    pass

class ApplyChangesToolCall(Event):
    pass

class ApplyChangesResult(Event):
    pass

class FileAssistantWorkflow(Workflow):
    def __init__(self, timeout: int = 300):
        super().__init__(timeout=timeout)
        self.llm = OpenAI(temperature=0.5, model="gpt-4o-mini")
        self.agent : FunctionAgent = get_agent(self.llm, [])

    @visible_step()
    async def get_tree(self, ev: StartEvent) -> TreeInputEvent:
        logging.info('HEre we are')
        return TreeInputEvent()

    @visible_step()
    async def agent_init(self, ev: TreeInputEvent) -> InputRequiredEvent:
        print('Running agent init')
        out = InputRequiredEvent(prefix='What\'s up?')
        # ctx.write_event_to_stream(out)
        return out

    @visible_step()
    async def determine_step(self, ctx: Context, ev: HumanResponseEvent) -> UnclearUserRequest | RequestedOperations | UserGivenConfirmation:    
        prompt = PromptTemplate(f"Please choose the next operation the user wants to take among the different choices: {ev.response}")
        output : StepChoice = self.llm.structured_predict(StepChoice, prompt)
        logging.info(f"Step choice: {output}")
        match output.type:
            case 'clarification':
                return UnclearUserRequest(text='Unclear')
            case 'operations':
                return RequestedOperations()
            case 'confirmation':
                return UserGivenConfirmation()
        return RequestedOperations()

    @visible_step()
    async def request_clarification(self, ev: UnclearUserRequest) -> InputRequiredEvent:
        return InputRequiredEvent(prefix='Could you clarify your request?')

    @visible_step()
    async def request_suggestions(self, ev: RequestedOperations) -> OperationSuggestion:
        return OperationSuggestion()

    @step
    async def request_confirmation(self, ev: OperationSuggestion) -> InputRequiredEvent:
        return InputRequiredEvent(prefix='Are you happy with the suggestions?')

    @visible_step()
    async def confirm(self, ev: UserGivenConfirmation) -> ApplyChangesToolCall:
        return ApplyChangesToolCall()

    @visible_step()
    async def apply_changes_tool(self, ev: ApplyChangesToolCall) -> ApplyChangesResult:
        return ApplyChangesResult()

    @step
    async def finish(self, ev: ApplyChangesResult) -> StopEvent:
        return StopEvent()

