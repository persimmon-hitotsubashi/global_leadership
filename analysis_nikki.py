import os

import openai
import pandas as pd
import requests
from PIL import Image
from io import BytesIO

openai.api_key = os.environ["OPENAI_API_KEY"]


class AnalyzeNikkiContents:

    def __init__(self) -> None:
        """
        SummarizeUrlContentsクラスのコンストラクタ.
        """
        self.openai_client = openai.OpenAI()

    def analysis(self, mindate, maxdate, analysis_point):
        date_Nikki = pd.read_csv("elly_Nikki.csv",
                                 encoding='utf-8',
                                 parse_dates=["date"])
        date_Nikki = date_Nikki.query("date >= @mindate and date < @maxdate")
        contents = dict(zip(date_Nikki["date"], date_Nikki["Nikki"]))
        system_template = self._setting_system_template(analysis_point)
        human_llm_template = self._setting_human_llm_template(contents,
                                                              analysis_point)
        messages = self._create_prompt_messages(system_template,
                                                human_llm_template)
        summmarize_result = openai.OpenAI().chat.completions.create(
            model="gpt-3.5-turbo-0125",
            # model="gpt-4-turbo-preview",
            temperature=0,
            max_tokens=4096,
            messages=messages,
            )
        return summmarize_result.choices[0].message.content

    @staticmethod
    def _create_prompt_messages(system_template: str,
                                user_template: str):
        """
        プロンプトメッセージを作成する関数.

        Args:
        ----
            system_template (str): システム側のプロンプトテンプレート。
            user_template (str): ユーザー側のプロンプトテンプレート。

        Returns:
        -------
            List[ChatCompletionMessageParam]: \
                システムとユーザーのプロンプトメッセージのリスト。
        """
        return [
            {"role": "system", "content": system_template},
            {"role": "user", "content": user_template},
        ]

    def _setting_system_template(self, analysis_point):
        return """\
        You are a helpful, skilled and prominent psychotherapist\
            in the United States.
        Your first task is to read a diary \
            and analyze the person's psychological state of {analysis_point}.
        You earn higher rewards for accurate and meticulous analysis.
        However, you are highly penalized \
            or are fired for poor quality analysis.
        """

    def _setting_human_llm_template(self, contents, analysis_point):

        return f"""\
        #### Your Tasks ####
        Your task is to read a diary \
            and analyze the person's psychological state of {analysis_point}.

        ================
        ####FOLLOWING ARTICLES#####

        {contents}
        ================
        ####CONSTRAINTS####

        日本語で200字程度で分析すること.
        The analysis should be approximately 200 words in Japanese.
        ================
        ####OUTPUT FORMAT####
        Return Analyze Output Only.
        """


class SuggestNikkiContents:

    def __init__(self) -> None:
        """
        SummarizeUrlContentsクラスのコンストラクタ.
        """
        self.openai_client = openai.OpenAI()

    def suggest(self, analysis_contents):
        system_template = self._setting_system_template()
        human_llm_template = self._setting_human_llm_template(
            analysis_contents)
        messages = self._create_prompt_messages(system_template,
                                                human_llm_template)
        summmarize_result = openai.OpenAI().chat.completions.create(
            model="gpt-3.5-turbo-0125",
            # model="gpt-4-turbo-preview",
            temperature=0,
            max_tokens=4096,
            messages=messages,
            )
        return summmarize_result.choices[0].message.content

    @staticmethod
    def _create_prompt_messages(system_template: str,
                                user_template: str):
        """
        プロンプトメッセージを作成する関数.

        Args:
        ----
            system_template (str): システム側のプロンプトテンプレート。
            user_template (str): ユーザー側のプロンプトテンプレート。

        Returns:
        -------
            List[ChatCompletionMessageParam]: \
                システムとユーザーのプロンプトメッセージのリスト。
        """
        return [
            {"role": "system", "content": system_template},
            {"role": "user", "content": user_template},
        ]

    def _setting_system_template(self):
        return """\
        You are a helpful, skilled and  prominent psychotherapist\
            in the United States.
        Your first task is to read the analysis of the diary \
            and give advice and encouragement.
        You earn higher rewards for good advice.
        However, you are highly penalized or are fired for poor quality advice.
        """

    def _setting_human_llm_template(self, contents):

        return f"""\
        #### Your Tasks ####
        Your first task is to read the analysis of the diary \
            and give advice and encouragement.

        ================
        ####FOLLOWING ARTICLES#####

        {contents}
        ================
        ####CONSTRAINTS####

        日本語で200字程度でアドバイスと励ましを生成してください.
        最後には必ず励ましの文面を書いてください.
        Generate advice and encouragement in about 200 characters in Japanese.
        Please be sure to include a note of encouragement at the end.
        ================
        ####OUTPUT FORMAT####
        Return Advice and encouragement Output Only.
        """


class CreateImageNikkiContents:

    def __init__(self) -> None:
        """
        SummarizeUrlContentsクラスのコンストラクタ.
        """
        self.openai_client = openai.OpenAI()

    def create_image(self, analysis_contents):
        human_llm_template = self._setting_human_llm_template(
            analysis_contents)

        response = self.openai_client.images.generate(
            model="dall-e-3",
            prompt=human_llm_template,
            size="1024x1024",
            quality="standard",
            n=1,
            )
        image_url = response.data[0].url
        response = requests.get(image_url)
        image_data = BytesIO(response.content)
        return Image.open(image_data)

    def _setting_human_llm_template(self, contents):

        return f"""\
        #### Your Tasks ####
        Your first task is to read the analysis of the diary \
            and to generate tarot card-like images in line with that analysis

        ================
        ####FOLLOWING ARTICLES#####

        {contents}
        ================
        """
