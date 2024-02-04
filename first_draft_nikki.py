import openai
import os
import base64
import requests

import pandas as pd

openai.api_key = os.environ["OPENAI_API_KEY"]
api_key = os.environ["OPENAI_API_KEY"]


class CreatefirstNikkiContents:

    def __init__(self) -> None:
        self.openai_client = openai.OpenAI()

    def create_main(self):
        encoded_images = self.pick_encode()
        picture_dict = self.description_image(encoded_images)
        schedule_dict = self.select_schedule()
        return self.create_draft(schedule_dict, picture_dict)

    def create_draft(self,
                     schedule_dict,
                     picture_dict):
        system_template = self._setting_system_template_draft()
        human_llm_template = self._setting_human_llm_template_draft(
            schedule_dict, picture_dict)
        messages = self._create_prompt_messages(
            system_template,
            human_llm_template)
        return self.openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            temperature=0,
            max_tokens=4096,
            messages=messages,
            ).choices[0].message.content

    def pick_encode(self):
        # 'Pictures' ディレクトリのパス
        directory = 'Picture'

        # ディレクトリ内のすべてのファイルを取得してエンコード
        encoded_images = {}
        for entry in os.scandir(directory):
            if entry.is_file():
                file_path = entry.path
                encoded_images[entry.name] = self.encode_image(file_path)
        return encoded_images

    @staticmethod
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    @staticmethod
    def description_image(encoded_images):
        picture_dict = {}
        for path, base64_image in encoded_images.items():
            prompt = """この写真は今日のあった出来事を取った写真です。
            この写真には何が写ってますか?
            """

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }

            payload = {
                "model": "gpt-4-vision-preview",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"{prompt}"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 1200
            }

            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

            picture_dict[path] = response.json().get("choices")[0]["message"]["content"]
        return picture_dict

    @staticmethod
    def select_schedule():
        df = pd.read_csv("elly_calendar.csv")
        return df.set_index('time', drop=False).T.to_dict('dict')

    def _setting_system_template_draft(self):
        return """\
        You are a helpful, skilled and prominent Diary writing assistant.
        Your task is to write a draft diary entry in 150 words.
        You earn higher rewards for good question and draft diary.
        However, you are highly penalized or are fired for poor quality question and draft diary.
        """

    def _setting_human_llm_template_draft(self, schedule_contents, photo_contents):

        return f"""\
        #### Your Tasks ####
        Your first task is to write a 150-word draft of diary \
            based on schedule and a description of the day's memorable photos.

        ================
        #### description of the day's memorable photos#####

        {photo_contents}
        ================
        #### schedule#####

        {schedule_contents}
        ================
        #### Output Example ####

        本日の予定としては、午前中に小学校で娘の劇の鑑賞会に行きました。
        娘は、劇でヒロインを演じていました。
        午後には夫と息子と合流し家族そろって、新宿でお洋服を買いに行きました。
        夜は、結婚記念日を記念して、家族で外食をしに行きました。

        #### CONSTRAINTS ####

        応答は必ず日本語ですること
        Responses must be in Japanese.
        写真の説明は不要です。
        No photo description is necessary.
        """

    def _create_prompt_messages(self,
                                system_template: str,
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
