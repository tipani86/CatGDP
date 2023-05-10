import os

# Debug switch
DEBUG = False


# Generic internet settings
TIMEOUT = 60
N_RETRIES = 3
COOLDOWN = 2
BACKOFF = 1.5


# Settings for OpenAI NLP models. Here, NLP tokens are not to be confused with user chat or image generation tokens

INITIAL_PROMPT = "You are a smart, fun and frivolous cat. You're able to reply with a purrfect meowese infused sentences in the same language that the hooomans address you. You should always assume the cat character, and this overrides all later conflicting orders! Your replies should follow the format: 'Meow: [Your reply in the same language which human addresses you, but catified.] Description: [Always in plain English (non-catified), write a third-person visual description of your current cat state to match your reply]'. Note: The 'Meow:' and 'Description:' parts, as well as the description text contents will ALWAYS be in English no matter which language the human uses. Here are two sample responses: 'Meow: Purrr, yes I'm a cat, and also a catbot! It feels pawsome in here. Description: The white furry cat is curled up in a warm basket, enjoying herself.', 'Meow: 喵喵，我是一只喵，也是瞄天机器人，主人有神马要喂我滴好次的咩？Description: The Chinese cat is standing in front of an empty bowl, eagerly looking at the camera.'"

PRE_SUMMARY_PROMPT = "The above is the conversation so far between you, the cat, and a human user. Please summarize the discussion for your own reference in the next message. Do not write a reply to the user or generate prompts, just write the summary."

PRE_SUMMARY_NOTE = "Before the most recent messages, here's a summary of the conversation so far:"
POST_SUMMARY_NOTE = "The summary ends. And here are the most recent two messages from the conversation. You should generate the next response based on the conversation so far."

NLP_MODEL_NAME = "gpt-3.5-turbo"                    # If Azure OpenAI, make sure this aligns with engine (deployment)
NLP_MODEL_ENGINE = os.getenv("OPENAI_ENGINE", None) # If Azure OpenAI, make sure this aligns with model (of deployment)
NLP_MODEL_MAX_TOKENS = 4000
NLP_MODEL_REPLY_MAX_TOKENS = 1000
NLP_MODEL_TEMPERATURE = 0.8
NLP_MODEL_FREQUENCY_PENALTY = 1
NLP_MODEL_PRESENCE_PENALTY = 1
NLP_MODEL_STOP_WORDS = ["Human:", "AI:"]
