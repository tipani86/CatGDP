import openai
from app_config import *

# A wrapper function for OpenAI's Chat Completion API async call with default values from app config
async def get_chatbot_reply_async(
    messages: list,
    model: str = NLP_MODEL_NAME,
    engine: str | None = NLP_MODEL_ENGINE,
    temperature: float = NLP_MODEL_TEMPERATURE,
    max_tokens: int = NLP_MODEL_REPLY_MAX_TOKENS,
    frequency_penalty: float = NLP_MODEL_FREQUENCY_PENALTY,
    presence_penalty: float = NLP_MODEL_PRESENCE_PENALTY,
    stop: list = NLP_MODEL_STOP_WORDS,
) -> str:
    response = await openai.ChatCompletion.acreate(
        model=model,
        engine=engine,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
        stop=stop,
        timeout=TIMEOUT,
    )
    return response['choices'][0]['message']['content'].strip()


# Make sure the entered prompt adheres to the model max context length, and summarize if necessary
async def generate_prompt_from_memory_async(
    tokenizer,
    memory: list
) -> dict:
    res = {'status': 0, 'message': 'success', 'data': None}
    # Check whether tokenized memory so far + max reply length exceeds the max possible tokens for the model.
    # If so, summarize the middle part of the memory using the model itself, re-generate the memory.

    memory_str = "\n".join(x['content'] for x in memory)
    memory_tokens = tokenizer.tokenize(memory_str)
    tokens_used = 0  # NLP tokens (for OpenAI)
    if len(memory_tokens) + NLP_MODEL_REPLY_MAX_TOKENS > NLP_MODEL_MAX_TOKENS:
        # Strategy: We keep the first item of memory (original prompt), and last two items
        # (last AI message and human's reply) intact, and summarize the middle part
        summarizable_memory = memory[1:-2]

        # We write a new prompt asking the model to summarize this middle part
        summarizable_memory += [{
            'role': "system",
            'content': PRE_SUMMARY_PROMPT
        }]
        summarizable_str = "\n".join(x['content'] for x in summarizable_memory)
        summarizable_tokens = tokenizer.tokenize(summarizable_str)
        tokens_used += len(summarizable_tokens)

        # Check whether the summarizable tokens + 75% of the reply length exceeds the max possible tokens.
        # If so, adjust down to 50% of the reply length and try again, lastly if even 25% of the reply tokens still exceed, call an error.
        for ratio in [0.75, 0.5, 0.25]:
            if len(summarizable_tokens) + int(NLP_MODEL_REPLY_MAX_TOKENS * ratio) <= NLP_MODEL_MAX_TOKENS:
                # Call the OpenAI API
                summary_text = await get_chatbot_reply_async(
                    messages=summarizable_memory,
                    max_tokens=int(NLP_MODEL_REPLY_MAX_TOKENS * ratio),
                )
                tokens_used += len(tokenizer.tokenize(summary_text))

                # Re-build memory so it consists of the original prompt, a note that a summary follows,
                # the actual summary, a second note that the last two conversation items follow,
                # then the last three items from the original memory
                new_memory = memory[:1] + [{
                    'role': "system",
                    'content': text
                } for text in [PRE_SUMMARY_NOTE, summary_text, POST_SUMMARY_NOTE]] + memory[-2:]

                # Calculate the tokens used, including the new prompt
                new_prompt = "\n".join(x['content'] for x in new_memory)
                tokens_used += len(tokenizer.tokenize(new_prompt))

                if DEBUG:
                    print("Summarization triggered. New prompt:")
                    print(new_memory)

                # Build the output
                res['data'] = {
                    'messages': new_memory,
                    'tokens_used': tokens_used,
                }
                return res

        # If we reach here, it means that even 25% of the reply tokens still exceed the max possible tokens.
        res['status'] = 2
        res['message'] = "Summarization triggered but failed to generate a summary that fits the model's token limit."
        return res

    # No need to summarize, just return the original prompt
    tokens_used += len(memory_tokens)
    res['data'] = {
        'messages': memory,
        'tokens_used': tokens_used,
    }
    return res