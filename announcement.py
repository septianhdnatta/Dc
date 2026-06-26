import discord
from discord.ext import commands
import os

# ================================
GUILD_ID = 1514258098217418772
RULES_CHANNEL_ID = 1518140282670157954
# ================================

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"✅ Login sebagai {bot.user}")
    print("📢 Bot siap digunakan!")


@bot.event
async def on_member_join(member: discord.Member):
    guild = member.guild
    welcome_ch = discord.utils.get(guild.text_channels, name="👋│welcome")
    rules_ch = guild.get_channel(RULES_CHANNEL_ID)

    # Auto-role Member
    member_role = discord.utils.get(guild.roles, name="Member")
    if member_role:
        await member.add_roles(member_role)

    if not welcome_ch:
        return

    embed = discord.Embed(
        title="👋 Selamat Datang!",
        description=f"Halo {member.mention}, selamat datang di **{guild.name}**!\nJangan lupa baca {rules_ch.mention} ya! 🎉",
        color=discord.Color.from_str("#23a55a")
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"Member ke-{guild.member_count}")

    await welcome_ch.send(embed=embed)


@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    if before.premium_since is None and after.premium_since is not None:
        guild = after.guild
        boost_ch = discord.utils.get(guild.text_channels, name="🚀│server-boost")
        if not boost_ch:
            return

        embed = discord.Embed(
            title="🚀 Server Boosted!",
            description=f"{after.mention} baru saja boost server ini!\nServer sekarang level **{guild.premium_tier}** dengan **{guild.premium_subscription_count}** boost 💜",
            color=discord.Color.from_str("#ff73fa")
        )
        embed.set_thumbnail(url=after.display_avatar.url)
        await boost_ch.send(embed=embed)


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


@bot.command(name="rules")
async def rules(ctx, *, isi: str):
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

    rules_ch = guild.get_channel(RULES_CHANNEL_ID)
    if rules_ch is None:
        await ctx.send("❌ Channel rules tidak ditemukan!")
        return

    embed = discord.Embed(
        title="📋 Rules Server",
        description=isi,
        color=discord.Color.from_str("#ff7043")
    )
    embed.set_footer(text="Harap patuhi rules yang berlaku!")

    await rules_ch.send(embed=embed)
    await ctx.send("✅ Rules berhasil dikirim!")


bot.run(os.environ.get("TOKEN"))
