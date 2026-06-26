import discord
from discord.ext import commands
import os

# ================================
GUILD_ID = 1514258098217418772
# ================================

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"✅ Login sebagai {bot.user}")
    print("📢 Bot announcement siap digunakan!")


@bot.command(name="anc")
async def announcement(ctx, *, pesan: str):
    if not isinstance(ctx.channel, discord.DMChannel):
        await ctx.send("❌ Command ini hanya bisa dipakai lewat DM bot!")
        return

    guild = bot.get_guild(GUILD_ID)
    if guild is None:
        await ctx.send("❌ Server tidak ditemukan!")
        return

    member = guild.get_member(ctx.author.id)
    if member is None:
        await ctx.send("❌ Kamu bukan member server!")
        return

    founder_role = discord.utils.get(guild.roles, name="Founder")
    if founder_role not in member.roles:
        await ctx.send("❌ Kamu tidak punya permission!")
        return

    announce_ch = discord.utils.get(guild.text_channels, name="📢│announcement")
    if announce_ch is None:
        await ctx.send("❌ Channel announcement tidak ditemukan!")
        return

    embed = discord.Embed(
        description=pesan,
        color=discord.Color.from_str("#5865f2")
    )
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    embed.set_footer(text="📢 Announcement")

    await announce_ch.send("@everyone", embed=embed)
    await ctx.send("✅ Announcement berhasil dikirim!")


bot.run(os.environ.get("TOKEN"))
