import asyncio
import traceback
from app_config import *


async def call_post_api_async(
    httpclient,
    url: str,
    headers: dict = None,
    data: dict = None,
) -> dict:
    res = {'status': 0, 'message': 'success', 'data': None}

    # Make an async post request to the API with timeout, retry, backoff etc.
    for i in range(N_RETRIES):
        try:
            if DEBUG:
                print(f"Attempt {i+1}: Calling API {url} with data {data}")
            async with httpclient.post(url, headers=headers, json=data, timeout=TIMEOUT) as response:
                if response.status == 200:
                    res['data'] = await response.json()
                    return res
                else:
                    if i == N_RETRIES - 1:
                        res['status'] = 2
                        res['message'] = f"API returned status code {response.status} and message {await response.text()} after {N_RETRIES} retries."
                        return res
                    else:
                        await asyncio.sleep(COOLDOWN + BACKOFF ** i)
        except:
            if i == N_RETRIES - 1:
                res['status'] = 2
                res['message'] = f"API call failed after {N_RETRIES}: {traceback.format_exc()}"
                return res
            else:
                await asyncio.sleep(COOLDOWN + BACKOFF ** i)

    res['status'] = 2
    res['message'] = f"Failed to call API after {N_RETRIES} retries."
    return res


async def generate_prompt_from_memory_async(
    httpclient,
    tokenizer,
    memory: list,
    api_key: str,
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
                url = "https://api.openai.com/v1/chat/completions"
                headers = {
                    'Content-Type': "application/json",
                    'Authorization': f"Bearer {api_key}",
                }
                data = {
                    'model': NLP_MODEL_NAME,
                    'messages': summarizable_memory,
                    'temperature': NLP_MODEL_TEMPERATURE,
                    'max_tokens': int(NLP_MODEL_REPLY_MAX_TOKENS * ratio),
                    'frequency_penalty': NLP_MODEL_FREQUENCY_PENALTY,
                    'presence_penalty': NLP_MODEL_PRESENCE_PENALTY,
                    'stop': NLP_MODEL_STOP_WORDS,
                }
                api_res = await call_post_api_async(httpclient, url, headers, data)
                if api_res['status'] != 0:
                    res['status'] = api_res['status']
                    res['message'] = api_res['message']
                    return res

                summary_text = api_res['data']['choices'][0]['message']['content'].strip()
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


async def get_chatbot_reply_data_async(
    httpclient,
    memory: list,
    api_key: str,
) -> dict:
    res = {'status': 0, 'message': "success", 'data': None}

    # Call the OpenAI API
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        'Content-Type': "application/json",
        'Authorization': f"Bearer {api_key}",
    }
    data = {
        'model': NLP_MODEL_NAME,
        'messages': memory,
        'temperature': NLP_MODEL_TEMPERATURE,
        'max_tokens': NLP_MODEL_REPLY_MAX_TOKENS,
        'frequency_penalty': NLP_MODEL_FREQUENCY_PENALTY,
        'presence_penalty': NLP_MODEL_PRESENCE_PENALTY,
        'stop': NLP_MODEL_STOP_WORDS,
    }
    api_res = await call_post_api_async(httpclient, url, headers, data)
    if api_res['status'] != 0:
        res['status'] = api_res['status']
        res['message'] = api_res['message']
        return res

    reply_text = api_res['data']['choices'][0]['message']['content'].strip()

    res['data'] = reply_text
    return res
