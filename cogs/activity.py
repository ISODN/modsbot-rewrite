import ast
import asyncio
import pickle
from datetime import datetime
import logging
import schedule
from discord.ext import commands

from cogs import config as cfg

Cog = commands.Cog

today_messages = {}


class Activity(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('cogs.activity')
        schedule.every().day.at("09:30").do(asyncio.run_coroutine_threadsafe, self.process_today(), bot.loop).tag(
            'cogs.activity')
        schedule.every(5).minutes.do(self.f_dump).tag('cogs.activity')

    async def process_today(self):
        today_date = datetime.now().strftime("%d %b %Y")
        self.logger.info(today_messages)

        # Figure out which users were active today.
        active_users_today = str(today_messages)

        await self.bot.get_channel(cfg.Config.config['log_channel']).send(
            "Logged active users for {}: ```{}```".format(today_date, active_users_today))

        # Log that information.
        r_body = {'values': [[today_date, str(active_users_today)]]}
        cfg.Config.service.spreadsheets().values().append(spreadsheetId=cfg.Config.config['activity_sheet'],
                                                          range='Log!A1', valueInputOption='RAW',
                                                          insertDataOption='INSERT_ROWS', body=r_body).execute()

        # Get the values of the previous 7 days.

        # Clear today's
        today_messages.clear()
        self.f_dump()

    @Cog.listener()
    async def on_message(self, message):
        if not message.author.bot and message.guild is not None:  # Ignore messages from bots and DMs
            if message.author.id in today_messages:
                today_messages[message.author.id] += 1
            else:
                today_messages[message.author.id] = 1

    @commands.command()
    @commands.is_owner()
    async def dump_activity(self, ctx):
        await ctx.send(today_messages)

    @commands.command()
    @commands.is_owner()
    async def add_activity(self, ctx, *, activity):
        try:
            activity_dict = ast.literal_eval(activity)
            for user in activity_dict:
                if user in today_messages:
                    today_messages[user] += activity_dict[user]
                else:
                    today_messages[user] = activity_dict[user]
            await ctx.send('Done!: New activity: ```{}```'.format(today_messages))
        except:
            await ctx.send("Something went wrong! ")

    @commands.command()
    @commands.is_owner()
    async def f_dump_activity(self, ctx):
        pickle.dump(today_messages, open('data/activity_dump.p', 'wb+'))
        await ctx.send("Dumped")

    def f_dump(self):
        pickle.dump(today_messages, open('data/activity_dump.p', 'wb+'))
        self.logger.info('Dumped activity: {}'.format(str(today_messages)))

    @commands.command()
    @commands.is_owner()
    async def f_load_activity(self, ctx):
        x = pickle.load(open('data/activity_dump.p', 'rb'))
        today_messages.clear()
        for i in x:
            today_messages[i] = x[i]
        await ctx.send("Loaded: ```{}```".format(today_messages))


def setup(bot):
    bot.add_cog(Activity(bot))
