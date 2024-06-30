""""
Copyright © Krypton 2019-2023 - https://github.com/kkrypt0nn (https://krypton.ninja)

Version: 6.1.0

Modified by Y.Ozaki - https://github.com/mttk1528
"""
from collections import defaultdict, deque
# from openai import OpenAI
from datetime import datetime
from discord.ext import commands
# from discord.ext import tasks
from discord.ext.commands import Context
from pprint import pprint
from typing import Union


# TODO: implement error handling
class GPTchat(commands.Cog, name="gptchat"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.openai_client = bot.openai_client

        self.server_to_gpt_model = defaultdict(lambda: "gpt-3.5-turbo")

        self.MAX_MEMORY = 20  # 20
        self._init_messages = [
            {
                "role": "system",
                "content": "あなたはの名前はかし子です。なによりもUserにとって親しみやすく、センスのある面白い人として振る舞うことが要求されています。また、常にクリエイティブでウィットに富む柔軟な思考を行ってください。常に敬語を用いてください。英語でのプロンプトには英語で答えてください。"
            },
            {
                "role": "user",
                "content": "こんにちは！"
            },
            {
                "role": "assistant",
                "content": "こんにちは！！今日は何についてお話ししましょうか？"
            }
        ]

        self.server_to_messages = defaultdict(lambda: deque(maxlen=(self.MAX_MEMORY + 1) * 2))

    # @tasks.loop(seconds=600)
    # async def loop_reset(self) -> None:
    #     for key, val in self.server_to_messages.items():
    #         self.server_to_messages[key] = self._init_messages.copy()

    @commands.hybrid_command(
        name="reset",
        description="This command resets the conversation.",
    )
    async def reset(self, context: Context) -> None:
        """
        This command resets the conversation.

        :param context: The application command context.
        """
        guild_id = context.guild.id
        # pprint(self.server_to_messages[guild_id])
        self.server_to_messages[guild_id] = deque(maxlen=(self.MAX_MEMORY + 1) * 2)
        if self.server_to_gpt_model[context.guild.id] == "gpt-4-turbo-preview":
            self.server_to_gpt_model[context.guild.id] = "gpt-3.5-turbo"

        await context.send("Successfully reset the conversation.")
        pprint(self.server_to_messages[guild_id])

    @commands.hybrid_command(
        name="model",
        description="This command shows the current GPT model.",
    )
    async def model(self, context: Context) -> None:
        """
        This is a testing command that does nothing.

        :param context: This command shows the current GPT model.
        """
        guild_id = context.guild.id
        mode = self.server_to_gpt_model[guild_id]
        await context.send(f"Current GPT model: {mode}")
        # pprint(self.server_to_messages[guild_id])

    async def generate_response(self, message: str, model: str = "gpt-3.5-turbo") -> Union[str, int, str, str, int, int, int]:
        """
        Generates a response to a given message.

        :param message: The message to generate a response to.
        :return: The generated response.
        """
        guild_id = message.guild.id
        self.server_to_messages[guild_id].append({
            "role": "user",
            "content": message.content
        })
        if self.server_to_messages[guild_id][0]["role"] == "assistant":
            self.server_to_messages[guild_id].popleft()

        all_messages = list(self._init_messages) + list(self.server_to_messages[guild_id])
        # pprint(self.server_to_messages[guild_id])
        response = await self.openai_client.chat.completions.create(
            model=model,
            messages=all_messages
        )
        answer = response.choices[0].message.content
        self.server_to_messages[guild_id].append({
            "role": "assistant",
            "content": answer
        })

        created_at = response.created
        model_info = response.model
        object_info = response.object
        completion_tokens = response.usage.completion_tokens
        prompt_tokens = response.usage.prompt_tokens
        total_tokens = response.usage.total_tokens

        result = {
            "answer": answer,
            "created_at": created_at,
            "model_info": model_info,
            "object_info": object_info,
            "completion_tokens": completion_tokens,
            "prompt_tokens": prompt_tokens,
            "total_tokens": total_tokens
        }

        return result

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Handles the on_message event.

        :param message: The message that was sent.
        """
        if message.author.bot:
            return
        if message.content.startswith("/"):
            return
        if message.content.startswith(self.bot.config["prefix"]):
            return
        if message.channel.id not in [1230828380291596329, 1230836921673191444]:
            return
        if message.content.startswith("*ig"):
            return

        print("-------------------------------------------------------------------")
        print(f"--- message by {message.author} (id: {message.author.id})  -> {message.content}")
        guild_id = message.guild.id
        model = self.server_to_gpt_model[guild_id]
        result = await self.generate_response(message, model)
        answer = result["answer"]
        created_at = result["created_at"]
        model_info = result["model_info"]
        object_info = result["object_info"]
        completion_tokens = result["completion_tokens"]
        prompt_tokens = result["prompt_tokens"]
        total_tokens = result["total_tokens"]

        print(f"- created : {datetime.fromtimestamp(created_at).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"- model   : {model_info}")
        print(f"- object  : {object_info}")
        print(f"- tokens  : {total_tokens} (completion: {completion_tokens}, prompt: {prompt_tokens})")
        print(f"--- response  -> {answer}")

        await self.bot.database.save_message(
            user_id=str(message.author.id),
            guild_id=str(message.guild.id),
            message=message.content,
            response=answer,
            created_at=datetime.fromtimestamp(created_at).strftime('%Y-%m-%d %H:%M:%S'),
            model_info=model_info,
            object_info=object_info,
            completion_tokens=completion_tokens,
            prompt_tokens=prompt_tokens,
            total_tokens=total_tokens
        )

        await message.channel.send(answer)

    @commands.hybrid_command(
        name="kasiko",
        description="This command does nothing.",
    )
    async def kasiko(self, context: Context) -> None:
        """
        This is a testing command that does nothing.

        :param context: The application command context.
        """
        if self.server_to_gpt_model[context.guild.id] == "gpt-3.5-turbo":
            self.server_to_gpt_model[context.guild.id] = "gpt-4-turbo-preview"
            await context.send("Changed model to gpt-4-turbo-preview")
        else:
            self.server_to_gpt_model[context.guild.id] = "gpt-3.5-turbo"
            await context.send("Changed model to gpt-3.5-turbo")

    # @commands.hybrid_command(
    #     name="init_messsaages",
    #     description="This function initializes the messages for the server.",
    # )
    # async def _init_messages.copy()(self, context: Context) -> None:


# And then we finally add the cog to the bot so that it can load, unload, reload and use it's content.
async def setup(bot) -> None:
    await bot.add_cog(GPTchat(bot))


