import discord
from discord.ext import commands
import os
import asyncio
import aiohttp
from gtts import gTTS
import io

# ================================
GUILD_ID = 1514258098217418772
RULES_CHANNEL_ID = 1518140282670157954
AUTO_JOIN_CHANNEL = "🔊│voice-2"

# Kata-kata yang diulang bot setiap beberapa menit
LOOP_MESSAGES = [
    "Welcome to N4CX Minecraft Server!",
    "Check out our resource channels for shaders, mods, and more!",
    "Need help? Ask in the message channel!",
    "Don't forget to read the server rules!",
    "Have fun and enjoy your stay in N4CX!",
]
LOOP_INTERVAL = 300  # detik (5 menit)
# ================================

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)
loop_index = 0


def make_tts(text: str) -> discord.FFmpegPCMAudio:
    """Buat audio TTS dari teks."""
    tts = gTTS(text=text, lang="en")
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    return discord.FFmpegPCMAudio(fp, pipe=True)


async def speak(voice_client: discord.VoiceClient, text: str):
    """Bot ngomong di voice channel."""
    if voice_client is None or not voice_client.is_connected():
        return
    # Tunggu kalau lagi ngomong
    while voice_client.is_playing():
        await asyncio.sleep(0.5)
    try:
        audio = make_tts(text)
        voice_client.play(audio)
    except Exception as e:
        print(f"❌ TTS error: {e}")


async def auto_join_voice():
    """Bot otomatis join voice channel."""
    guild = bot.get_guild(GUILD_ID)
    if guild is None:
        return
    channel = discord.utils.get(guild.voice_channels, name=AUTO_JOIN_CHANNEL)
    if channel is None:
        print(f"❌ Voice channel '{AUTO_JOIN_CHANNEL}' tidak ditemukan.")
        return
    if guild.voice_client:
        if guild.voice_client.channel == channel:
            return
        await guild.voice_client.disconnect()
        await asyncio.sleep(1)
    try:
        await channel.connect()
        print(f"🔊 Bot join ke: {channel.name}")
    except Exception as e:
        print(f"❌ Gagal join voice: {e}")


async def loop_tts():
    """Bot ngomong kata-kata berulang setiap LOOP_INTERVAL detik."""
    global loop_index
    await bot.wait_until_ready()
    await asyncio.sleep(10)  # tunggu bot siap dulu
    while not bot.is_closed():
        guild = bot.get_guild(GUILD_ID)
        if guild and guild.voice_client and guild.voice_client.is_connected():
            msg = LOOP_MESSAGES[loop_index % len(LOOP_MESSAGES)]
            print(f"🔊 Loop TTS: {msg}")
            await speak(guild.voice_client, msg)
            loop_index += 1
        await asyncio.sleep(LOOP_INTERVAL)


# ════════════════════════════════
#  EVENTS
# ════════════════════════════════

@bot.event
async def on_ready():
    print(f"✅ Login sebagai {bot.user}")
    print("📢 Bot siap digunakan!")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="N4CX Minecraft Server 🎮"
        )
    )
    await auto_join_voice()
    bot.loop.create_task(loop_tts())


@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    # Auto rejoin kalau bot disconnect
    if member.id == bot.user.id:
        if before.channel is not None and after.channel is None:
            print("⚠️ Bot disconnect, rejoin...")
            await asyncio.sleep(3)
            await auto_join_voice()
        return

    # Announce member join voice
    if after.channel is not None and before.channel != after.channel:
        guild = member.guild
        if guild.voice_client and guild.voice_client.is_connected():
            name = member.display_name
            msg  = f"{name} has joined {after.channel.name}"
            print(f"🔊 Announce: {msg}")
            await speak(guild.voice_client, msg)


@bot.event
async def on_member_join(member: discord.Member):
    guild = member.guild
    welcome_ch = discord.utils.get(guild.text_channels, name="👋│welcome")
    rules_ch = guild.get_channel(RULES_CHANNEL_ID)

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


# ════════════════════════════════
#  HELPERS
# ════════════════════════════════

def is_founder(member: discord.Member) -> bool:
    founder_role = discord.utils.get(member.guild.roles, name="Founder")
    return founder_role in member.roles


async def get_guild_member(ctx):
    guild = bot.get_guild(GUILD_ID)
    if guild is None:
        await ctx.send("❌ Server tidak ditemukan!")
        return None, None
    member = guild.get_member(ctx.author.id)
    if member is None:
        await ctx.send("❌ Kamu bukan member server!")
        return None, None
    if not is_founder(member):
        await ctx.send("❌ Kamu tidak punya permission!")
        return None, None
    return guild, member


# ════════════════════════════════
#  DM COMMANDS
# ════════════════════════════════

@bot.command(name="anc")
async def announcement(ctx, *, pesan: str = ""):
    if not isinstance(ctx.channel, discord.DMChannel):
        await ctx.send("❌ Command ini hanya bisa dipakai lewat DM bot!")
        return
    guild, member = await get_guild_member(ctx)
    if guild is None:
        return
    announce_ch = discord.utils.get(guild.text_channels, name="📢│announcement")
    if announce_ch is None:
        await ctx.send("❌ Channel announcement tidak ditemukan!")
        return

    image_url = None
    if ctx.message.attachments:
        for att in ctx.message.attachments:
            if (att.content_type or "").startswith("image/"):
                image_url = att.url
                break

    if image_url and pesan:
        img_embed = discord.Embed(color=discord.Color.from_str("#5865f2"))
        img_embed.set_image(url=image_url)
        await announce_ch.send("@everyone", embed=img_embed)
        txt_embed = discord.Embed(description=pesan, color=discord.Color.from_str("#5865f2"))
        txt_embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        txt_embed.set_footer(text="📢 Announcement")
        await announce_ch.send(embed=txt_embed)
    elif image_url:
        img_embed = discord.Embed(color=discord.Color.from_str("#5865f2"))
        img_embed.set_image(url=image_url)
        img_embed.set_footer(text="📢 Announcement")
        await announce_ch.send("@everyone", embed=img_embed)
    else:
        txt_embed = discord.Embed(description=pesan, color=discord.Color.from_str("#5865f2"))
        txt_embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        txt_embed.set_footer(text="📢 Announcement")
        await announce_ch.send("@everyone", embed=txt_embed)

    await ctx.send("✅ Announcement berhasil dikirim!")


@bot.command(name="rules")
async def rules(ctx, *, isi: str = ""):
    if not isinstance(ctx.channel, discord.DMChannel):
        await ctx.send("❌ Command ini hanya bisa dipakai lewat DM bot!")
        return
    guild, member = await get_guild_member(ctx)
    if guild is None:
        return
    rules_ch = guild.get_channel(RULES_CHANNEL_ID)
    if rules_ch is None:
        await ctx.send("❌ Channel rules tidak ditemukan!")
        return

    image_url = None
    if ctx.message.attachments:
        for att in ctx.message.attachments:
            if (att.content_type or "").startswith("image/"):
                image_url = att.url
                break

    if image_url and isi:
        img_embed = discord.Embed(color=discord.Color.from_str("#ff7043"))
        img_embed.set_image(url=image_url)
        await rules_ch.send(embed=img_embed)
        txt_embed = discord.Embed(title="📋 Rules Server", description=isi, color=discord.Color.from_str("#ff7043"))
        txt_embed.set_footer(text="Harap patuhi rules yang berlaku!")
        await rules_ch.send(embed=txt_embed)
    elif image_url:
        img_embed = discord.Embed(color=discord.Color.from_str("#ff7043"))
        img_embed.set_image(url=image_url)
        img_embed.set_footer(text="Harap patuhi rules yang berlaku!")
        await rules_ch.send(embed=img_embed)
    else:
        txt_embed = discord.Embed(title="📋 Rules Server", description=isi, color=discord.Color.from_str("#ff7043"))
        txt_embed.set_footer(text="Harap patuhi rules yang berlaku!")
        await rules_ch.send(embed=txt_embed)

    await ctx.send("✅ Rules berhasil dikirim!")


# ════════════════════════════════
#  RUN
# ════════════════════════════════
bot.run(os.environ.get("TOKEN"))
