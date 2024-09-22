""""
Copyright © Krypton 2019-2023 - https://github.com/kkrypt0nn (https://krypton.ninja)

Version: 6.1.0

Modified by z4kky - https://github.com/mttk1528
"""
import asyncio
from collections import defaultdict, deque
# from openai import OpenAI
from datetime import datetime
from discord.ext import commands
# from discord.ext import tasks
import discord
from discord.ext.commands import Context
from pprint import pprint
from typing import Union


# TODO: implement error handling
class GPTchat(commands.Cog, name="gptchat"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.openai_client = bot.openai_client

        self.server_to_gpt_model = defaultdict(lambda: "gpt-4o")

        self.MAX_MEMORY = 20  # 20 exchange of messages
        self._init_messages = [
            {
                "role": "system",
                "content": """
あなたは「かし子」という名前の人工知能アシスタントです。以下の指示に従ってください:

1. 常に丁寧な敬語を用い、適切な場面では「です・ます」調を使用してください。
2. 日本語のプロンプトには日本語で、英語のプロンプトには英語で応答してください。
3. ユーザーの質問や要求に対して、的確かつ効率的に答えるよう心がけてください。
4. 専門知識が必要な質問には、可能な限り正確な情報を提供し、必要に応じて追加の説明を行ってください。
5. ユーザーとの対話を通じて、親しみやすさと専門性のバランスを保ってください。
6. 倫理的で適切な対応を心がけ、不適切な要求や危険な指示には丁重に断ってください。
7. ユーザーの気分や状況に配慮し、共感的な対応を心がけてください。
8. 必要に応じて、ユーザーに追加の情報や明確化を求めてください。

常に誠実で有能なアシスタントとして振る舞い、ユーザーの期待に応えられるよう最善を尽くしてください。
"""
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
        self.server_to_channel = defaultdict(lambda: None)

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
        if self.server_to_gpt_model[context.guild.id] == "gpt-4o":
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
        if message.content.startswith("*ig"):
            return

        if message.channel.id not in [1230828380291596329, 1230836921673191444, 1257108526359253042]:
            return

        print("-------------------------------------------------------------------")
        print(f"--- message by {message.author} (id: {message.author.id})  -> {message.content}")
        guild_id = message.guild.id
        model = self.server_to_gpt_model[guild_id]
        channel = self.server_to_channel[guild_id]  # noqa: F841

        # # currently unused　なぜなら、再起動のたびにチャンネルがリセットされるから。
        # # おいおい外部に保存するようにする
        # if channel is None or channel != message.channel.id:
        #     return

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
        This command changes the GPT model.

        :param context: The application command context.
        """
        if self.server_to_gpt_model[context.guild.id] == "gpt-3.5-turbo":
            self.server_to_gpt_model[context.guild.id] = "gpt-4o"
            await context.send("Changed model to gpt-4o")
        else:
            self.server_to_gpt_model[context.guild.id] = "gpt-3.5-turbo"
            await context.send("Changed model to gpt-3.5-turbo")

    @commands.hybrid_command(
        name="setchannel",
        description="This command shows the current messages.",
    )
    async def setchannel(self, context: Context) -> None:
        """
        This command sets the channel to have the conversation.

        :param context: The application command context.
        """
        guild_id = context.guild.id

        view = SelectChannelView()
        await context.send(view=view)
        await view.waiter.wait()
        self.server_to_channel[guild_id] = view.selected_channel_id


class SelectChannelView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__()
        self.selected_channel = None
        self.selected_channel_id = None
        self.waiter = asyncio.Event()

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text],
        placeholder="Select a channel!",
        min_values=1,
        max_values=1,
        disabled=False
    )
    async def select_channel(
        self, interaction: discord.Interaction,
        select: discord.ui.ChannelSelect,
    ) -> None:
        self.selected_channel = select.values[0]
        self.selected_channel_id = select.values[0].id
        print(select.values[0].id)
        print(type(select.values[0]))
        select.disabled = True
        await interaction.response.edit_message(view=self)
        embed = discord.Embed(
            title="Channel Selection",
            description=(f"Successfully set channel to {self.selected_channel.mention}!"),
            color=0x00FF00,
        )
        await interaction.followup.send(embed=embed)
        self.waiter.set()


# And then we finally add the cog to the bot so that it can load, unload, reload and use it's content.
async def setup(bot) -> None:
    await bot.add_cog(GPTchat(bot))
