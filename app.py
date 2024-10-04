
import streamlit as st
import openai
import os
import glob

# テキストデータの読み込み関数
@st.cache_data
def load_all_texts(folder_path):
    abs_folder_path = os.path.join(os.path.dirname(__file__), folder_path)

    # フォルダ内の全てのテキストファイルを取得
    text_files = glob.glob(os.path.join(abs_folder_path, "*.txt"))
    
    all_texts = ""
    for file_path in text_files:
        # Shift-JISで読み込む
        with open(file_path, "r", encoding="shift_jis") as file:
            all_texts += file.read() + "\n"  # 各ファイルの内容を結合
    
    return all_texts

# 森鴎外の作品を格納したフォルダからテキストを読み込む
all_mori_ogai_texts = load_all_texts("txtfile_129")


# Streamlit Community Cloudの「Secrets」からOpenAI API keyを取得
openai.api_key = st.secrets.OpenAIAPI.openai_api_key

# st.session_stateを使いメッセージのやりとりを保存
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "system", "content": st.secrets.AppSettings.chatbot_setting} 
    ]
    
# チャットボットとやりとりする関数
def communicate():
    messages = st.session_state["messages"]

    user_message = {"role": "user", "content": st.session_state["user_input"]}
    messages.append(user_message)

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    bot_message = response["choices"][0]["message"]
    messages.append(bot_message)

    st.session_state["user_input"] = ""  # 入力欄を消去


# ユーザーインターフェイスの構築
st.title("森鴎外AIアシスタント")
st.write("森鴎外の作品に基づくチャットボットです。")

user_input = st.text_input("メッセージを入力してください。", key="user_input", on_change=communicate)

if st.session_state["messages"]:
    messages = st.session_state["messages"]

    for message in reversed(messages[1:]):  # 直近のメッセージを上に
        speaker = "🙂"
        if message["role"]=="assistant":
            speaker="🤖"

        st.write(speaker + ": " + message["content"])
