import os
import json
import streamlit as st
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate

st.set_page_config(
    page_title="Quiz Generator", 
    page_icon="🧠"
    )

function = {
    "name": "create_quiz",
    "description": "function that takes a list of questions and answers and returns a quiz",
    "parameters": {
        "type": "object",
        "properties": {
            "questions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                        },
                        "answers": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "answer": {
                                        "type": "string",
                                    },
                                    "correct": {
                                        "type": "boolean",
                                    },
                                },
                                "required": ["answer", "correct"],
                            },
                        },
                    },
                    "required": ["question", "answers"],
                },
            }
        },
        "required": ["questions"],
    },
}

llm = None
if os.environ.get("OPENAI_API_KEY"):
    llm = ChatOpenAI(
        model_name="gpt-4o-mini-2024-07-18",
        temperature=0.1,
    ).bind(
        function_call={"name": "create_quiz"},
        functions=[function],
    )

if llm:
    prompt = PromptTemplate.from_template("Make a quiz about {topic} in {quiz_level}")
    chain = prompt | llm 


@st.cache_data(show_spinner="Quiz Generating...")
def generate_quiz_cached(topic: str, quiz_level: str):
    return chain.invoke({"topic": topic, "quiz_level": quiz_level})

def trigger_quiz(topic, quiz_level):
    result = generate_quiz_cached(topic, quiz_level)
    result_str = result.additional_kwargs["function_call"]["arguments"]
    result_dict = json.loads(result_str) 
    st.session_state.quiz_result = result_dict
    return result_dict




st.title("🧠 Quiz Generator")

with st.sidebar:
    st.markdown("https://github.com/oguhn/quiz_generator/blob/main/app.py")
    st.header("Settings")
    api_key = st.text_input("OpenAI API 키를 입력하세요", type="password", key="api_key")
    if st.button("확인"):
        if api_key:
            st.session_state.api_key_valid = True
            os.environ["OPENAI_API_KEY"] = api_key
        else:
            st.error("API 키를 입력해주세요.")

    if not api_key or not st.session_state.get("api_key_valid", False):
        st.error("OpenAI API 키를 입력하고 확인 버튼을 눌러주세요.")
        st.stop()

    quiz_level = st.selectbox("Quiz Level", ["Easy", "Hard"])
    topic = st.text_input("Topic",  placeholder="Please enter a topic")

    button_label = "다시 만들기" if "quiz_result" in st.session_state else "Generate Quiz"
    generate_quiz_button = st.sidebar.button(button_label)


if topic and generate_quiz_button:
    response = trigger_quiz(topic, quiz_level)
    st.session_state.quiz_triggered = True

if st.session_state.get("quiz_result"):
    response = st.session_state.quiz_result
    with st.form("questions_form"):
        for question in response["questions"]:
            st.write(question["question"])
            value = st.radio(
                "Select an option.",
                [answer["answer"] for answer in question["answers"]],
                index=None,
                key=question["question"] 
            )
            if {"answer": value, "correct": True} in question["answers"]:
                st.success("Correct!")
            elif value is not None:
                st.error("Wrong!")
        button = st.form_submit_button()
        if button:
            all_correct = True
            for question in response["questions"]:
                selected = st.session_state.get(question["question"])
                if not {"answer": selected, "correct": True} in question["answers"]:
                    all_correct = False
                    break
            if all_correct:
                st.balloons()
