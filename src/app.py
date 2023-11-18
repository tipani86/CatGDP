import os
import base64
import asyncio
import traceback
from PIL import Image
import streamlit as st
from transformers import AutoTokenizer
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
from google.protobuf.json_format import MessageToJson
from app_config import *
from utils import *

# Set global variables

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ["TOKENIZERS_PARALLELISM"] = "false"


# Check environment variables

errors = []
for key in [
    "OPENAI_API_KEY", "OPENAI_API_BASE", "OPENAI_API_TYPE", # For OpenAI APIs
    "STABILITY_HOST", "STABILITY_API_KEY",                  # For Stability APIs
]:
    if key not in os.environ:
        errors.append(f"Please set the {key} environment variable.")
if len(errors) > 0:
    st.error("\n".join(errors))
    st.stop()

stability_api = client.StabilityInference(
    key=os.environ['STABILITY_API_KEY'],  # API Key reference.
    # verbose=True,  # Print debug messages.
    engine="stable-diffusion-xl-1024-v1-0", # Set the engine to use for generation.
    # Available engines: stable-diffusion-xl-1024-v0-9 stable-diffusion-v1 stable-diffusion-v1-5 stable-diffusion-512-v2-0 stable-diffusion-768-v2-0
    # stable-diffusion-512-v2-1 stable-diffusion-768-v2-1 stable-diffusion-xl-beta-v2-2-2 stable-inpainting-v1-0 stable-inpainting-512-v2-0
)

### FUNCTION DEFINITIONS ###


@st.cache_data(show_spinner=False)
def get_local_img(file_path: str) -> str:
    # Load a byte image and return its base64 encoded string
    return base64.b64encode(open(file_path, "rb").read()).decode("utf-8")


@st.cache_data(show_spinner=False)
def get_favicon(file_path: str):
    # Load a byte image and return its favicon
    return Image.open(file_path)


@st.cache_data(show_spinner=False)
def get_tokenizer():
    return AutoTokenizer.from_pretrained("gpt2", low_cpu_mem_usage=True)


@st.cache_data(show_spinner=False)
def get_css() -> str:
    # Read CSS code from style.css file
    with open(os.path.join(ROOT_DIR, "src", "style.css"), "r") as f:
        return f"<style>{f.read()}</style>"


def get_chat_message(
    contents: str = "",
    align: str = "left"
) -> str:
    # Formats the message in an chat fashion (user right, reply left)
    div_class = "AI-line"
    color = "rgb(240, 242, 246)"
    file_path = os.path.join(ROOT_DIR, "src", "assets", "AI_icon.png")
    src = f"data:image/gif;base64,{get_local_img(file_path)}"
    if align == "right":
        div_class = "human-line"
        color = "rgb(165, 239, 127)"
        if "USER" in st.session_state:
            src = st.session_state.USER.avatar_url
        else:
            file_path = os.path.join(ROOT_DIR, "src", "assets", "user_icon.png")
            src = f"data:image/gif;base64,{get_local_img(file_path)}"
    icon_code = f"<img class='chat-icon' src='{src}' width=32 height=32 alt='avatar'>"
    formatted_contents = f"""
    <div class="{div_class}">
        {icon_code}
        <div class="chat-bubble" style="background: {color};">
        &#8203;{contents}
        </div>
    </div>
    """
    return formatted_contents


async def main(human_prompt: str) -> dict:
    res = {'status': 0, 'message': "Success"}
    try:

        # Strip the prompt of any potentially harmful html/js injections
        human_prompt = human_prompt.replace("<", "&lt;").replace(">", "&gt;")

        # Update both chat log and the model memory
        st.session_state.LOG.append(f"Human: {human_prompt}")
        st.session_state.MEMORY.append({'role': "user", 'content': human_prompt})

        # Clear the input box after human_prompt is used
        prompt_box.empty()

        with chat_box:
            # Write the latest human message first
            line = st.session_state.LOG[-1]
            contents = line.split("Human: ")[1]
            st.markdown(get_chat_message(contents, align="right"), unsafe_allow_html=True)

            reply_box = st.empty()
            reply_box.markdown(get_chat_message(), unsafe_allow_html=True)

            # This is one of those small three-dot animations to indicate the bot is "writing"
            writing_animation = st.empty()
            file_path = os.path.join(ROOT_DIR, "src", "assets", "loading.gif")
            writing_animation.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;<img src='data:image/gif;base64,{get_local_img(file_path)}' width=30 height=10>", unsafe_allow_html=True)

            # Step 1: Generate the AI-aided image prompt using ChatGPT API
            # (but we first need to generate the prompt for ChatGPT!)
            prompt_res = await generate_prompt_from_memory_async(
                TOKENIZER,
                st.session_state.MEMORY
            )

            if DEBUG:
                with st.sidebar:
                    st.write("prompt_res")
                    st.json(prompt_res, expanded=False)

            if prompt_res['status'] != 0:
                res['status'] = prompt_res['status']
                res['message'] = prompt_res['message']
                return res
            
            # Update the memory from prompt res
            st.session_state.MEMORY = prompt_res['data']['messages']

            # Call the OpenAI ChatGPT API
            chatbot_response = await get_chatbot_reply_async(
                st.session_state.MEMORY
            )

            if DEBUG:
                with st.sidebar:
                    st.write("chatbot_response")
                    st.json({'str': chatbot_response}, expanded=False)

            if "Description:" in chatbot_response:
                reply_text, image_prompt = chatbot_response.split("Description:")
            else:
                reply_text = chatbot_response
                image_prompt = f"Photorealistic image of a cat. {reply_text}"

            if reply_text.startswith("Meow: "):
                reply_text = reply_text.split("Meow: ", 1)[1]

            # Step 2: Generate the image using Stable Diffusion
            api_res = stability_api.generate(
                prompt=image_prompt,
                steps=30,
                # width=512,
                # height=512,
                samples=1,
            )

            if DEBUG:
                with st.sidebar:
                    st.write("stability_api_res")

            b64str = None
            for resp in api_res:
                for artifact in resp.artifacts:
                    if artifact.finish_reason == generation.FILTER:
                        st.warning("Your request activated the API's safety filters and could not be processed. Please modify the prompt and try again.")
                        # st.stop()
                    if artifact.type == generation.ARTIFACT_IMAGE:
                        b64str = base64.b64encode(artifact.binary).decode("utf-8")

                        if DEBUG:
                            with st.sidebar:
                                st.json(MessageToJson(resp), expanded=False)

                        break

            # Render the reply as chat reply
            message = f"{reply_text}"
            if b64str:
                message += f"""<br><img src="data:image/png;base64,{b64str}" width=256 height=256 alt="AI Generated Image">"""
            if DEBUG:
                message += f"""<br>{image_prompt}"""
            reply_box.markdown(get_chat_message(message), unsafe_allow_html=True)

            # Clear the writing animation
            writing_animation.empty()

            # Update the chat log and the model memory
            st.session_state.LOG.append(f"AI: {message}")
            st.session_state.MEMORY.append({'role': "assistant", 'content': reply_text})

    except:
        res['status'] = 2
        res['message'] = traceback.format_exc()

    return res

### INITIALIZE AND LOAD ###

# Initialize page config
favicon = get_favicon(os.path.join(ROOT_DIR, "src", "assets", "AI_icon.png"))
st.set_page_config(
    page_title="CatGDP - Feline whiskerful conversations.",
    page_icon=favicon,
)

# Get query parameters
query_params = st.experimental_get_query_params()
if "debug" in query_params and query_params["debug"][0].lower() == "true":
    st.session_state.DEBUG = True

if "DEBUG" in st.session_state and st.session_state.DEBUG:
    DEBUG = True


# Initialize some useful class instances
with st.spinner("Initializing App..."):
    TOKENIZER = get_tokenizer()  # First time after deployment takes a few seconds


### MAIN STREAMLIT UI STARTS HERE ###


# Define main layout
st.title("Meow")
st.subheader("I iz CatGDP, meow-speak anypawdy to me and I'll purr-ly there with a paw-some meow reply. 🐱")
st.subheader("")
chat_box = st.container()
st.write("")
prompt_box = st.empty()
footer = st.container()

with footer:
    st.markdown("""
    <div align=right><small>
    Page views: <img src="https://www.cutercounter.com/hits.php?id=hvxndaff&nd=5&style=1" border="0" alt="hit counter"><br>
    Unique visitors: <img src="https://www.cutercounter.com/hits.php?id=hxndkqx&nd=5&style=1" border="0" alt="website counter"><br>
    GitHub <a href="https://github.com/tipani86/CatGDP"><img alt="GitHub Repo stars" src="https://img.shields.io/github/stars/tipani86/CatGDP?style=social"></a>
    </small></div>
    """, unsafe_allow_html=True)

if DEBUG:
    with st.sidebar:
        st.subheader("Debug area")


# Load CSS code
st.markdown(get_css(), unsafe_allow_html=True)


# Initialize/maintain a chat log and chat memory in Streamlit's session state
# Log is the actual line by line chat, while memory is limited by model's maximum token context length
if "MEMORY" not in st.session_state:
    st.session_state.MEMORY = [{'role': "system", 'content': INITIAL_PROMPT}]
    st.session_state.LOG = [INITIAL_PROMPT]


# Render chat history so far
with chat_box:
    for line in st.session_state.LOG[1:]:
        # For AI response
        if line.startswith("AI: "):
            contents = line.split("AI: ")[1]
            st.markdown(get_chat_message(contents), unsafe_allow_html=True)

        # For human prompts
        if line.startswith("Human: "):
            contents = line.split("Human: ")[1]
            st.markdown(get_chat_message(contents, align="right"), unsafe_allow_html=True)


# Define an input box for human prompts
with prompt_box:
    human_prompt = st.text_input("Purr:", value="", key=f"text_input_{len(st.session_state.LOG)}")


# Gate the subsequent chatbot response to only when the user has entered a prompt
if len(human_prompt) > 0:
    run_res = asyncio.run(main(human_prompt))
    if run_res['status'] == 0 and not DEBUG:
        st.experimental_rerun()

    else:
        if run_res['status'] != 0:
            st.error(run_res['message'])
        with prompt_box:
            if st.button("Show text input field"):
                st.experimental_rerun()
