""""
Copyright © Krypton 2019-2023 - https://github.com/kkrypt0nn (https://krypton.ninja)

Version: 6.1.0

Modified by Y.Ozaki - https://github.com/mttk1528
"""


import aiosqlite


class DatabaseManager:
    def __init__(self, *, connection: aiosqlite.Connection) -> None:
        self.connection = connection

    async def save_message(self, user_id: str, guild_id: str, message: str, response: str, created_at: str, model_info: str, object_info: str, completion_tokens: int, prompt_tokens: int, total_tokens: int) -> None:
        """
        Saves a message and its response along with other metadata to the database.

        :param user_id: The ID of the user who sent the message.
        :param guild_id: The ID of the guild where the message was sent.
        :param message: The content of the message.
        :param response: The content of the bot's response.
        :param created_at: The creation date of the response.
        :param model_info: The model used to generate the response.
        :param object_info: Additional object information from the API.
        :param completion_tokens: Number of tokens used for completion.
        :param prompt_tokens: Number of tokens used for the prompt.
        :param total_tokens: Total number of tokens used.
        """
        await self.connection.execute(
            "INSERT INTO messages (user_id, guild_id, message, response, created_at, model_info, object_info, completion_tokens, prompt_tokens, total_tokens) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, guild_id, message, response, created_at, model_info, object_info, completion_tokens, prompt_tokens, total_tokens)
        )
        await self.connection.commit()

    async def get_messages(self, user_id: str, guild_id: str) -> list:
        """
        Retrieves all messages and responses for a specific user and guild.

        :param user_id: The ID of the user.
        :param guild_id: The ID of the guild.
        :return: A list of messages and responses.
        """
        rows = await self.connection.execute(
            "SELECT user_id, guild_id, message, response FROM messages WHERE user_id=? AND guild_id=?",
            (user_id, guild_id)
        )
        return await rows.fetchall()
