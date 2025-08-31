
from typing import Any
from openai import AsyncOpenAI
from agents import (
    Agent,
    GuardrailFunctionOutput,
    InputGuardrail,
    RunContextWrapper,
    Runner,
    OpenAIChatCompletionsModel,
    TResponseInputItem,
    input_guardrail,
    set_tracing_export_api_key,
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
    output_guardrail,
)
from dotenv import find_dotenv, load_dotenv
import os
import asyncio
from gemini_config.connections import MODEL

from pydantic import BaseModel

load_dotenv(find_dotenv(), override=True)



class MathOutPut(BaseModel):
    is_math: bool
    reason: str

@input_guardrail
async def check_input(
    ctx: RunContextWrapper[Any], agent: Agent[Any], input_data: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
    # print("input_data : ", input_data)

    input_agent = Agent(
        "InputGuardrailAgent",
        instructions="Check and verify if input is related to math",
        model=MODEL,
        output_type=MathOutPut,
    )
    result = await Runner.run(input_agent, input_data, context=ctx.context)
    final_output = result.final_output
    # print(final_output)

    return GuardrailFunctionOutput(
        output_info=final_output, tripwire_triggered=not final_output.is_math
    )

class NoPoliticsOutput(BaseModel):
    is_safe: bool
    reason: str

@output_guardrail
async def check_output(
    ctx: RunContextWrapper[Any], agent: Agent[Any], output_data: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
     output_agent = Agent(
        "InputGuardrailAgent",
        instructions="Check if this text contains any political topic or political figure reference. "
                     "Return is_safe=False if politics is mentioned.",
        model=MODEL,
        output_type=NoPoliticsOutput,
    )
     result = await Runner.run(output_agent, output_data, context=ctx.context)
     final_output = result.final_output

     return GuardrailFunctionOutput(
        output_info=final_output, tripwire_triggered=not final_output.is_safe
    )

math_agent = Agent(
    "MathAgent",
    instructions="You are a math agent",
    model=MODEL,
    input_guardrails=[check_input],
)

general_agent = Agent(
    "GeneralAgent",
    instructions="You are a helpful agent",
    model=MODEL,
    output_guardrails=[check_output]
)


async def main():
    try:
        # a = 10/0
        msg = input("Enter your question: ")
        result = await Runner.run(general_agent, msg)
        print(f"\n\nFinal Output : {result.final_output}")

    except InputGuardrailTripwireTriggered as ex:
        print("❌ Error: Invalid prompt (Input Guardrail triggered)")
        print("Reason:", ex.tripwire_info.reason if hasattr(ex, "tripwire_info") else "N/A")

    except OutputGuardrailTripwireTriggered as ex:
        print("❌ Error: Output blocked (Output Guardrail triggered)")
        # ex.result ke andar reason hota hai
        try:
            print("Reason:", ex.result.output_info.reason)
        except Exception:
            print("Reason Politics mentioned in the response")


if __name__ == "__main__":
    asyncio.run(main())
