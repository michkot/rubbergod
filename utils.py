from datetime import datetime

import git
import discord
from discord import Member
from discord.ext import commands

from config.messages import Messages
from config.app_config import Config


def generate_mention(user_id):
    return '<@' + str(user_id) + '>'


def git_hash():
    repo = git.Repo(search_parent_directories=True)
    return repo.head.object.hexsha


def git_commit_msg():
    repo = git.Repo(search_parent_directories=True)
    return repo.head.commit.message


def git_pull():
    repo = git.Repo(search_parent_directories=True)
    cmd = repo.git
    return cmd.pull()


def id_to_datetime(snowflake_id: int):
    return datetime.fromtimestamp(((snowflake_id >> 22) + 1420070400000) / 1000)


def str_emoji_id(emoji):
    if isinstance(emoji, int):
        return str(emoji)

    return emoji if isinstance(emoji, str) else str(emoji.id)


def has_role(user, role_name: str):
    if type(user) != Member:
        return None

    return role_name.lower() in [x.name.lower() for x in user.roles]


def fill_message(message_name, *args, **kwargs):
    """Fills message template from messages by attempting to get the attr.
    :param message_name: {str} message template name
    :kwargs: {dict} data for formatting the template
    :return: filled template
    """

    # Convert username/admin to a mention
    if 'user' in kwargs:
        kwargs['user'] = generate_mention(kwargs['user'])

    if 'admin' in kwargs:
        kwargs['admin'] = generate_mention(kwargs['admin'])

    to_escape = ['role', 'not_role', 'line']

    for arg in to_escape:
        if arg in kwargs:
            kwargs[arg] = discord.utils.escape_mentions(kwargs[arg])

    # Attempt to get message template and fill
    try:
        template = getattr(Messages, message_name)
        return template.format(*args, **kwargs)
    except AttributeError:
        raise ValueError("Invalid template {}".format(message_name))


def pagination_next(emoji, page, max_page):
    if emoji in ["▶", "🔽"]:
        next_page = page + 1
    elif emoji in ["◀", "🔼"]:
        next_page = page - 1
    elif emoji == "⏪":
        next_page = 1
    if 1 <= next_page <= max_page:
        return next_page
    else:
        return 0


def is_bot_owner(ctx: commands.Context):
    return ctx.author.id == Config.admin_id


def cut_string(string: str, part_len: int):
    return list(string[0+i:part_len+i] for i in range(0, len(string), part_len))


async def reaction_get_ctx(bot, payload):
    channel = bot.get_channel(payload.channel_id)
    if channel is None:
        return None
    if channel.type is discord.ChannelType.text:
        guild = channel.guild
    else:
        guild = bot.get_guild(Config.guild_id)
        if guild is None:
            raise Exception("Nemůžu najít guildu podle config.guild_id")
    member = guild.get_member(payload.user_id)

    try:
        message = await channel.fetch_message(payload.message_id)
    except discord.errors.NotFound:
        return None

    if member is None or message is None or member.bot:
        return None

    if payload.emoji.is_custom_emoji():
        emoji = bot.get_emoji(payload.emoji.id)
        if emoji is None:
            emoji = payload.emoji
    else:
        emoji = payload.emoji.name

    return dict(channel=channel, guild=guild, member=member, message=message, emoji=emoji)


class NotHelperPlusError(commands.CommandError):
    """An error indicating that a user doesn't have permissions to use
    a command that is available only to helpers, submods and mods.
    """


async def helper_plus(ctx):
    allowed_roles = {Config.mod_role, Config.submod_role, Config.helper_role}
    for role in ctx.author.roles:
        if role.id in allowed_roles:
            return True
    raise NotHelperPlusError
