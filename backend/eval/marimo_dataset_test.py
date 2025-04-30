

import marimo

__generated_with = "0.13.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return


@app.cell
def _():
    import nest_asyncio
    from eval.conversation_utils import format_conversation, format_conversation_nested_message
    from app.instrument import PROJECT_NAME
    from datetime import datetime, timedelta
    nest_asyncio.apply()
    return (
        PROJECT_NAME,
        datetime,
        format_conversation_nested_message,
        timedelta,
    )


@app.cell
def _():
    import phoenix as px
    client = px.Client()
    # Get the current dataset version
    dataset = client.get_dataset(id="RGF0YXNldDoz", version_id="RGF0YXNldFZlcnNpb246Ng==")
    return client, px


@app.cell
def _():
    from phoenix.trace.dsl import SpanQuery
    import json
    return SpanQuery, json


@app.cell
def _():
    import pandas as pd
    return (pd,)


@app.cell
def _(datetime, timedelta):
    start = datetime.now() - timedelta(days=4)
    end = datetime.now() - timedelta(days=0)
    return


@app.cell
def _(SpanQuery):
    llm_query = SpanQuery().select(
        'span_id',
        'parent_id',
        'llm.input_messages',
        messages='input.messages',
        input="input.value",
        output="output.value"
    ).where('span_kind == "llm"')\
        .where('metadata["qualia.workflow.id"] == "orchestrate_suggest_workflow"')\
        .where('"astream_chat" in name')
    query_for_parent_with_agent_info = SpanQuery().select(
        'span_kind',
        'parent_id',
        'span_id',
        parent_output='output',
        # span_id="parent_id",
    )
    return llm_query, query_for_parent_with_agent_info


@app.cell
def _(PROJECT_NAME, client, llm_query, query_for_parent_with_agent_info):
    llm_spans_df = client.query_spans(llm_query, project_name=PROJECT_NAME)
    parent_spans_df = client.query_spans(query_for_parent_with_agent_info, project_name=PROJECT_NAME)
    return llm_spans_df, parent_spans_df


@app.cell
def _(llm_spans_df, parent_spans_df, pd, try_get_agent_name):
    llm_spans_with_parent = pd.merge(llm_spans_df, parent_spans_df, how='inner', left_on='parent_id', right_index=True)
    llm_spans_with_parent = llm_spans_with_parent.assign(current_agent_name=llm_spans_with_parent.parent_output.apply(try_get_agent_name))
    return (llm_spans_with_parent,)


@app.cell
def _(llm_spans_with_parent):
    llm_spans_with_parent.groupby('current_agent_name').count()
    return


@app.cell
def _(json):
    def try_get_agent_name(x):
        if isinstance(x, dict) and 'value' in x:
            try:
                result = json.loads(x['value'])
                return result['current_agent_name']
            except:
                pass
        return None
    return (try_get_agent_name,)


@app.cell
def _(
    OpenAIModel,
    USER_FRUSTRATION_PROMPT_TEMPLATE,
    df,
    llm_classify,
    model,
    rails,
):
    eval_model = OpenAIModel(model="gpt-4o")

    relevance_classifications = llm_classify(
        dataframe=df,
        template=USER_FRUSTRATION_PROMPT_TEMPLATE,
        model=model,
        rails=rails,
        provide_explanation=True, #optional to generate explanations for the value produced by the eval LLM
    )
    return (relevance_classifications,)


@app.cell
def _(llm_spans_with_parent):
    llm_spans_with_parent

    return


@app.function
def task(x):
    return {'error': 'yes'}


@app.cell
def _():
    from eval.evaluators import no_error, has_results
    return


@app.cell
def _():
    # from phoenix.experiments import run_experiment
    # experiment = run_experiment(dataset, task=task, evaluators=[no_error, has_results], dry_run=False)
    return


@app.cell
def _():
    # from phoenix.experiments.evaluators import HelpfulnessEvaluator
    # from phoenix.evals.models import OpenAIModel


    # helpfulness_evaluator = HelpfulnessEvaluator(model=OpenAIModel())
    return


@app.cell
def _():
    from phoenix.experiments import run_experiment, MatchesRegex

    # This defines a code evaluator for links
    contains_link = MatchesRegex(
        pattern=r"[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)",
        name="contains_link"
    )
    return


@app.cell
def _(format_conversation_nested_message, llm_spans_with_parent):
    conversation_df = llm_spans_with_parent.copy()
    conversation_df['conversation'] = conversation_df['llm.input_messages'].apply(lambda x: format_conversation_nested_message(x))
    return (conversation_df,)


@app.cell
def _(conversation_df):
    conversation_df
    return


@app.cell
def _(conversation_df):
    from phoenix.evals import (
        USER_FRUSTRATION_PROMPT_RAILS_MAP,
        USER_FRUSTRATION_PROMPT_TEMPLATE,
        OpenAIModel,
        llm_classify,
    )

    model = OpenAIModel(
        model="gpt-4",
        temperature=0.0,
    )

    #The rails is used to hold the output to specific values based on the template
    #It will remove text such as ",,," or "..."
    #Will ensure the binary value expected from the template is returned
    rails = list(USER_FRUSTRATION_PROMPT_RAILS_MAP.values())
    relevance_classifications = llm_classify(
        data=conversation_df,
        template=USER_FRUSTRATION_PROMPT_TEMPLATE,
        model=model,
        rails=rails,
        provide_explanation=True, #optional to generate explanations for the value produced by the eval LLM
    )
    return (
        OpenAIModel,
        USER_FRUSTRATION_PROMPT_TEMPLATE,
        llm_classify,
        model,
        rails,
        relevance_classifications,
    )


@app.cell
def _(relevance_classifications):
    relevance_classifications
    return


@app.cell
def _(px, relevance_classifications):
    from phoenix.trace import SpanEvaluations

    px.Client().log_evaluations(
        SpanEvaluations(eval_name="USER_FRUSTRATION_gpt-4", dataframe=relevance_classifications)
    )
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
