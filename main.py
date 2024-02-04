from pathlib import Path

import datetime
from PIL import Image
from dateutil.relativedelta import relativedelta
import pandas as pd
from time import sleep
import streamlit as st
import streamlit_authenticator as stauth
import yaml

from analysis_nikki import (AnalyzeNikkiContents,
                            SuggestNikkiContents,
                            CreateImageNikkiContents)
from assistant_nikki import WritingNikkiContents
from first_draft_nikki import CreatefirstNikkiContents

# yamlファイルからユーザー情報を読み込む
with Path.open(Path("users.yaml")) as file:
    config = yaml.safe_load(file)

nikki_im = Image.open("nikki_logo.jpg")

st.set_page_config(page_title="Nikki",
                   page_icon=nikki_im)
st.sidebar.title("Nav")

authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
)


def upload_csv(label: str):
    """
    Streamlitを使用してCSVファイルをアップロードする関数.

    :param label: アップローダーのラベル
    :return: アップロードされたファイル
    """
    return st.file_uploader(label=label, type="csv",
                            accept_multiple_files=False)


def upload_picture(label: str):
    """
    Streamlitを使用してCSVファイルをアップロードする関数.

    :param label: アップローダーのラベル
    :return: アップロードされたファイル
    """
    return st.file_uploader(label=label, type=["jpeg", "png", "gif"],
                            accept_multiple_files=True)


def create_self_content(date):
    st.header("本日のNikkeyを書いてみましょう")
    with st.form(key="self_Nikki", clear_on_submit=False):
        st.write(
            """
            本日のNikkiを入力してください。
            """,
        )
        today_Nikki = st.text_area(
            label=f"{date}のNikki:", key="self_Nikki_prompt", height=5,
        )
        submit_button = st.form_submit_button(label="Submit")
        if submit_button:
            st.write("本日もお疲れ様でした。")
            st.session_state.today_Nikki = today_Nikki
            st.experimental_rerun()


def create_ai_content():
    if "first_draft" in st.session_state:
        generate_start()
    else:
        # タブコンテンツの作成ロジック
        st.header("写真やスケジュールをもとに、Nikkiの草稿を作成します。")
        with st.container(border=True):
            st.write("生成AIで草稿を作成します。")
            # schedule_csv = upload_csv("本日のスケジュールをアップロードしてください")
            # upload_pictures = upload_picture("本日の思い出写真をアップロードしてください。")
            submit_button = st.button(label="Generate Start")

        if submit_button:
            with st.spinner("日記のdraftを作成しています。\n 今日はどんな1日でしたか。"):
                st.session_state.first_draft = \
                    CreatefirstNikkiContents().create_main()
            st.experimental_rerun()


def generate_start():
    if "draft_diary" in st.session_state:
        conversation_message()
    else:
        st.write("生成AIが作成した日記のdraftです。")
        with st.container(border=True):
            st.write(st.session_state.first_draft)
        ai_msg = "今日の感情を教えてください"
        st.write(ai_msg)
        ai_message = [{"AImessage": st.session_state.first_draft},
                      {"AImessage": ai_msg}]
        st.session_state.assistant = WritingNikkiContents(ai_message)
        with st.form(key="conversation_Nikki", clear_on_submit=False):
            feeling = st.radio("感情:", ("楽しい", "嬉しい", "哀しい", "イライラ", "退屈"))
            feeling_temperature = st.slider(
                "", min_value=1.0, max_value=5.0, value=3.0, step=1.00
            )
            submit_button = st.form_submit_button(label="submit")
        if submit_button:
            with st.spinner("日記のdraftを作成しています.毎日振り返りをするのは大事です"):
                user_feeling = f"今日の感情は{feeling}が1から5の5段階で\
                    {feeling_temperature}でした。"
                st.session_state.draft_diary \
                    = st.session_state.assistant.create_draft(user_feeling)
                st.session_state.conversation_memory \
                    = st.session_state.assistant.conversation()
            st.experimental_rerun()


def conversation_message():
    st.write("生成AIが作成したOutputです。")
    with st.container(border=True):
        st.write(st.session_state.draft_diary)
    st.header("本日のNikkeyを書いてみましょう")
    with st.form(key="self_Nikki_ai", clear_on_submit=False):
        st.write(
            """
            本日のNikkiを入力してください。
            """,
        )
        today_Nikki = st.text_area(
            label="本日のNikki:", key="self_Nikki_prompt_ai", height=5,
        )
        submit_button = st.form_submit_button(label="Submit")

    st.header("生成AIと会話を続ける")
    with st.form(key="conversation", clear_on_submit=True):
        st.write(
            f"""
            Assistantからの質問
            {list(st.session_state.conversation_memory[-1].values())[0]}
            """,
        )
        response_Nikki = st.text_area(
            label="Response:", key="conversation_response", height=5,
        )
        conversation_button = st.form_submit_button(label="Conversation")
    if submit_button:
        if today_Nikki:
            st.write("本日もお疲れ様でした。")
            st.session_state.today_Nikki = today_Nikki
        else:
            st.warning("本日のNikkiが入力されていません。")
    if conversation_button:
        if response_Nikki:
            with st.spinner("生成AIと通信中"):
                st.session_state.draft_diary \
                    = st.session_state.assistant.create_draft(response_Nikki)
                st.session_state.conversation_memory \
                    = st.session_state.assistant.conversation()
            st.experimental_rerun()
        else:
            st.warning("Responseが入力されていません。")
    display_chat_message()


def display_chat_message():
    # チャット履歴の表示
    for message in st.session_state.get("conversation_memory", []):
        if list(message.keys())[0] == "AImessage":
            with st.chat_message("assistant"):
                st.markdown(list(message.values())[0])
        if list(message.keys())[0] == "UserMessage":
            with st.chat_message("user"):
                st.markdown(list(message.values())[0])


def view_paste_content(date):
    # タブコンテンツの作成ロジック
    today_date = datetime.date.today()
    date_Nikki = pd.read_csv("elly_Nikki.csv",
                             encoding='utf-8',
                             parse_dates=["date"])
    st.write(f"{date.strftime('%m-%d')}の日記")
    date1yearago = date - relativedelta(years=1)
    date2yearago = date - relativedelta(years=2)
    date3yearago = date - relativedelta(years=3)
    st.write(f"{date3yearago}の日記")
    with st.container(border=True):
        st.write(str(date_Nikki.query("date == @date3yearago")["Nikki"].iloc[0]))
    st.write(f"{date2yearago}の日記")
    with st.container(border=True):
        st.write(str(date_Nikki.query("date == @date2yearago")["Nikki"].iloc[0]))
    st.write(f"{date1yearago}の日記")
    with st.container(border=True):
        st.write(str(date_Nikki.query("date == @date1yearago")["Nikki"].iloc[0]))
    if date < today_date:
        st.write(f"{date}の日記")
        with st.container(border=True):
            st.write(str(date_Nikki.query("date == @date")["Nikki"].iloc[0]))


def viewing_writing_Nikki() -> None:
    st.title("Nikkiを見る、書く")
    today_date = datetime.date.today()
    min_date = datetime.date(2024, 1, 27)
    max_date = datetime.date(2024, 2, 10)
    date = st.date_input('', today_date, min_value=min_date, max_value=max_date)
    view_paste_content(date)

    if date == today_date:
        if "today_Nikki" in st.session_state:
            st.write(f"{today_date}の日記")
            with st.container(border=True):
                st.write(st.session_state.today_Nikki)
        else:
            tab_titles = ["AI Assistant", "自筆"]
            tabs = st.tabs(tab_titles)

            with tabs[0]:
                create_ai_content()

            with tabs[1]:
                create_self_content(date)


def analysis_Nikki_content(content):
    st.header(f"あなたのNikkiを{content}単位で分析します")
    with st.form(key=f"analyze_dairy_{content}", clear_on_submit=False):
        analysis_points = ["well-being", "人間関係", "家族との関係",
                           "仕事関係", "学び", "思考のバイアス/癖"]
        selected_points = st.multiselect('分析する観点を選択', analysis_points,
                                         default=["well-being", "学び", "思考のバイアス/癖"])
        submit_button = st.form_submit_button(label="Analyze start")
    if submit_button:
        last_month = datetime.date.today() - relativedelta(month=1)
        if content == "3ヶ月":
            col_headers_1 = f"{(last_month - relativedelta(years=1) - relativedelta(month=9)).strftime('%Y-%m')}~\
                {(last_month - relativedelta(years=1) - relativedelta(month=6)).strftime('%Y-%m')}"
            col_headers_2 = f"{(last_month - relativedelta(years=1) - relativedelta(month=5)).strftime('%Y-%m')}~\
                {(last_month - relativedelta(years=1) - relativedelta(month=3)).strftime('%Y-%m')}"
            col_headers_3 = f"{(last_month - relativedelta(years=1) - relativedelta(month=2)).strftime('%Y-%m')}~\
                {last_month.strftime('%Y-%m')}"
        if content == "6ヶ月":
            col_headers_1 = f"{(last_month - relativedelta(years=2) + relativedelta(month=8)).strftime('%Y-%m')}~\
                {(last_month - relativedelta(years=1)).strftime('%Y-%m')}"
            col_headers_2 = f"{(last_month - relativedelta(years=1) + relativedelta(month=2)).strftime('%Y-%m')}~\
                {(last_month - relativedelta(years=1) + relativedelta(month=7)).strftime('%Y-%m')}"
            col_headers_3 = f"{(last_month - relativedelta(years=1) + relativedelta(month=8)).strftime('%Y-%m')}~\
                {last_month.strftime('%Y-%m')}"
        if content == "1年":
            col_headers_1 = f"{(last_month - relativedelta(years=3)).strftime('%Y-%m')}~\
                {(last_month - relativedelta(years=2) - relativedelta(month=1)).strftime('%Y-%m')}"
            col_headers_2 = f"{(last_month - relativedelta(years=2)).strftime('%Y-%m')}~\
                {(last_month - relativedelta(years=1) - relativedelta(month=1)).strftime('%Y-%m')}"
            col_headers_3 = f"{(last_month - relativedelta(years=1)).strftime('%Y-%m')}~\
                {last_month.strftime('%Y-%m')}"

        analyze_contents = {}
        with st.spinner("あなたのNikkiを分析しています"):
            # 画面を3分割する
            col1, col2, col3 = st.columns(3)

            # 最初の列にコンテンツを配置
            with col1:
                analyze_contents_sub = {}
                min_date = datetime.date.today() - relativedelta(years=3)
                max_date = datetime.date.today() - relativedelta(years=2)
                analyze_Nikki = AnalyzeNikkiContents()
                st.write(f"""期間:{col_headers_1}""")
                with st.spinner("analyze_contents"):
                    for point in selected_points:
                        analyze_text = analyze_Nikki.analysis(min_date,
                                                              max_date,
                                                              point)
                        analyze_contents_sub[point] = analyze_text
                    image_ = CreateImageNikkiContents().create_image(analyze_contents_sub)
                st.image(image_, caption=f"""{col_headers_1}のタロットカード風""")
                for key, value in analyze_contents_sub.items():
                    st.write(f"**{key}**")
                    st.write(value)
                analyze_contents[col_headers_1] = analyze_contents_sub

            # 2番目の列にコンテンツを配置
            with col2:
                analyze_contents_sub = {}
                min_date = datetime.date.today() - relativedelta(years=2)
                max_date = datetime.date.today() - relativedelta(years=1)
                st.write(f"""期間:{col_headers_2}""")
                analyze_Nikki = AnalyzeNikkiContents()
                with st.spinner("analyze_contents"):
                    for point in selected_points:
                        analyze_text = analyze_Nikki.analysis(min_date,
                                                              max_date,
                                                              point)
                        analyze_contents_sub[point] = analyze_text
                    image_ = CreateImageNikkiContents().create_image(analyze_contents_sub)
                st.image(image_, caption=f"""{col_headers_1}のタロットカード風""")
                for key, value in analyze_contents_sub.items():
                    st.write(f"**{key}**")
                    st.write(value)
                analyze_contents[col_headers_2] = analyze_contents_sub

            # 3番目の列にコンテンツを配置
            with col3:
                min_date = datetime.date.today() - relativedelta(years=1)
                max_date = datetime.date.today()
                st.write(f"""期間:{col_headers_3}""")
                analyze_Nikki = AnalyzeNikkiContents()
                with st.spinner("analyze_contents"):
                    for point in selected_points:
                        analyze_text = analyze_Nikki.analysis(min_date,
                                                              max_date,
                                                              point)
                        analyze_contents_sub[point] = analyze_text
                    image_ = CreateImageNikkiContents().create_image(analyze_contents_sub)
                st.image(image_, caption=f"""{col_headers_1}のタロットカード風""")
                for key, value in analyze_contents_sub.items():
                    st.write(f"**{key}**")
                    st.write(value)
                analyze_contents[col_headers_3] = analyze_contents_sub
        st.header("アドバイスコメント")
        suggest_Nikki = SuggestNikkiContents()
        suggest_text = suggest_Nikki.suggest(analyze_contents)
        st.write(suggest_text)


def analysis_Nikki() -> None:
    st.title("Nikkiを分析する")

    tab_titles = ["3Month", "6Month", "1Year"]
    tabs = st.tabs(tab_titles)

    with tabs[0]:
        analysis_Nikki_content("3ヶ月")

    with tabs[1]:
        analysis_Nikki_content("6ヶ月")

    with tabs[2]:
        analysis_Nikki_content("1年")


def main():
    # ユーザーのログイン処理
    authenticator.login()
    # ユーザー認証の結果に基づいて処理を分岐
    if st.session_state["authentication_status"]:
        # ユーザーログアウト処理。ログアウト時に認証情報をNoneにリセット
        authenticator.logout("Logout", "sidebar")
        # サイドバーにナビゲーションオプションを表示
        selection = st.sidebar.radio(
            "Go to",
            [
                "Writing Nikki",
                "Analysis me",
            ],
        )
        # 選択されたオプションに基づいて対応するページへの処理を実行
        if selection == "Writing Nikki":
            viewing_writing_Nikki()
        elif selection == "Analysis me":
            analysis_Nikki()

    # 認証失敗時のエラーメッセージ
    elif st.session_state["authentication_status"] is False:
        st.error("Username or password is incorrect. Please try again.")
    # 認証情報が未入力の場合の警告メッセージ
    elif st.session_state["authentication_status"] is None:
        st.warning("Please enter your username and password to continue.")


if __name__ == "__main__":
    main()
