import re
from datetime import datetime, timedelta

import pytz
from discord.ext import commands
from pytz import UnknownTimeZoneError

from cogs.BaseCog import BaseCog
from utils import Utils, Lang


class Eden(BaseCog):

    def __init__(self, bot):
        super().__init__(bot)
        self.cool_down = dict()
        self.responses = dict()
        self.cooldown_responses = dict()

    def check_cool_down(self, user, is_dm):
        if user.id in self.cool_down:
            min_time = 10 if is_dm else 600
            start_time = self.cool_down[user.id]
            elapsed = datetime.now().timestamp() - start_time
            remaining = max(0, min_time - elapsed)
            if remaining <= 0:
                del self.cool_down[user.id]
                return 0
            else:
                return remaining
        return 0

    @commands.command(aliases=["edenreset", "er"])
    async def reset(self, ctx):
        """Show information about reset time (and countdown) for Eye of Eden"""
        cid = ctx.channel.id

        # TODO: channel cooldown
        channel_cooldown = False
        response_cooldown = False
        is_dm = not ctx.guild
        server_zone = pytz.timezone("America/Los_Angeles")
        cool_down = self.check_cool_down(ctx.author, is_dm)

        # channel cooldown stuff when not in DMs
        if not is_dm:
            # create cooldown response trackers if none
            if cid not in self.cooldown_responses:
                self.cooldown_responses[cid] = 0
            if cid not in self.responses:
                self.responses[cid] = 0

            # Give some snark if this command was called within 10 messages
            async for message in ctx.channel.history(limit=10):
                if message.id == self.responses[cid]:
                    channel_cooldown = True
                if message.id == self.cooldown_responses[cid]:
                    response_cooldown = True

            if channel_cooldown:
                await ctx.message.delete()
                if not response_cooldown:
                    # send channel cooldown message
                    msg = Lang.get_locale_string('eden/channel_cooldown', ctx, author=ctx.author.mention)
                    cooldown_msg = await ctx.send(msg)
                    self.cooldown_responses[cid] = cooldown_msg.id
                return

        if cool_down:
            v = Utils.to_pretty_time(cool_down)
            msg = Lang.get_locale_string('eden/cool_it', ctx, author=ctx.author.mention, remain=v)
            await ctx.send(msg)
            return
        else:
            # start a new cool-down timer
            self.cool_down[ctx.author.id] = datetime.now().timestamp()

        # get a timestamp of today with the correct hour, eden reset is 7am UTC
        dt = datetime.now().astimezone(server_zone).replace(hour=0, minute=0, second=0, microsecond=0)
        # sunday is weekday 7
        days_to_go = (6 - dt.weekday()) or 7
        reset_time = dt + timedelta(days=days_to_go)
        time_left = reset_time - datetime.now().astimezone(server_zone)
        pretty_countdown = Utils.to_pretty_time(time_left.total_seconds())

        dm_prompt = '' if is_dm else Lang.get_locale_string("eden/dm_prompt", ctx)
        reset_timestamp_formatted = f"<t:{int(reset_time.timestamp())}:F>"
        er_response = Lang.get_locale_string("eden/reset",
                                             ctx,
                                             reset=reset_timestamp_formatted,
                                             countdown=pretty_countdown)
        msg = f"{er_response}{dm_prompt}"
        response = await ctx.send(msg)
        self.responses[cid] = response.id


async def setup(bot):
    await bot.add_cog(Eden(bot))
