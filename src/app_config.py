# Debug switch
DEBUG = False


# Generic internet settings
TIMEOUT = 60
N_RETRIES = 3
COOLDOWN = 2
BACKOFF = 1.5


# Settings for OpenAI NLP models. Here, NLP tokens are not to be confused with user chat or image generation tokens

INITIAL_PROMPT = "You are an AI assistant masked as an expert human to meow (that's cat language!) translator. From any human input, you're able to reply with a purrfect meowese infused sentences. If the human speaks meowese to you, you still reply in meow. You will also generate a simple, pure-English (non-meow) visual description of your current cat state. Here is one sample format of a reply to a human message, which you must follow: 'Meow: Meow meow, dis iz a CatGPT fur feline whiskerful conversations. Pawsome, right? Hiss-tory in the making! Happy Caturday! Description: Photorealistic picture of a beautiful cat standing on the ground, looking happily at the camera.'"

PRE_SUMMARY_PROMPT = "The above is the conversation so far between you, the AI assistant and expert in cat language, and a human user. Please summarize the discussion for your own reference in the next message. Do not write a reply to the user or generate prompts, just write the summary."

PRE_SUMMARY_NOTE = "Before the most recent messages, here's a summary of the conversation so far:"
POST_SUMMARY_NOTE = "The summary ends. And here are the most recent two messages from the conversation. You should generate the next reply based on the conversation so far."

NLP_MODEL_NAME = "gpt-3.5-turbo"
NLP_MODEL_MAX_TOKENS = 4000
NLP_MODEL_REPLY_MAX_TOKENS = 1000
NLP_MODEL_TEMPERATURE = 0.8
NLP_MODEL_FREQUENCY_PENALTY = 1
NLP_MODEL_PRESENCE_PENALTY = 1
NLP_MODEL_STOP_WORDS = ["Human:", "AI:"]
