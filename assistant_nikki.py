import os

import openai

openai.api_key = os.environ["OPENAI_API_KEY"]


class WritingNikkiContents:

    def __init__(self, ai_message) -> None:
        """
        SummarizeUrlContentsクラスのコンストラクタ.
        """
        self.openai_client = openai.OpenAI()
        self.conversation_memory = ai_message

    def conversation(self):
        system_template = self._setting_system_template_question()
        human_llm_template = self._setting_human_llm_template_question(
            self.conversation_memory)
        messages = self._create_prompt_messages(system_template,
                                                human_llm_template)
        ai_message = openai.OpenAI().chat.completions.create(
            model="gpt-4-turbo-preview",
            temperature=0,
            max_tokens=4096,
            messages=messages,
            )
        self.conversation_memory.append({"AImessage": ai_message.choices[0].message.content})
        return self.conversation_memory

    def create_draft(self, user_input):
        self.conversation_memory.append({"UserMessage": user_input})
        system_template = self._setting_system_template_draft()
        human_llm_template = self._setting_human_llm_template_draft(
            self.conversation_memory)
        messages = self._create_prompt_messages(system_template,
                                                human_llm_template)
        return self.openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            temperature=0,
            max_tokens=4096,
            messages=messages,
            ).choices[0].message.content

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

    def _setting_system_template_draft(self):
        return """\
        You are a helpful, skilled and prominent Diary writing assistant.
        Your task is to write a draft diary entry in 150 words.
        You earn higher rewards for good draft diary.
        However, you are highly penalized or are fired for poor quality draft diary.
        """

    def _setting_system_template_question(self):
        return """\
        You are a helpful, skilled and prominent Diary writing assistant.
        Your task is to ask questions about the user's feelings \
            and thoughts at the time.
        You earn higher rewards for good question.
        However, you are highly penalized or are fired for poor quality question.
        """

    def _setting_human_llm_template_draft(self, contents):

        return f"""\
        #### Your Tasks ####
        Your first task is to write a 150-word draft of diary \
            based on our conversation history.

        ================
        #### Conversation history#####

        {contents}
        ================
        #### CONSTRAINTS ####

        応答は必ず日本語ですること
        Responses must be in Japanese.
        """

    def _setting_human_llm_template_question(self, contents):

        return f"""\
        #### Your Tasks ####
        Your first task is to ask questions about the user's feelings \
            and thoughts at the time.

        ================
        #### Conversation history #####

        {contents}
        ================
        #### CONSTRAINTS ####

        応答は必ず日本語ですること
        Responses must be in Japanese.
        """
