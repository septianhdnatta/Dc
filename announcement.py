import discord
from discord.ext import commands
import os
import asyncio

# ================================
GUILD_ID = 1514258098217418772
RULES_CHANNEL_ID = 1518140282670157954
AUTO_JOIN_CHANNEL = "🔊│voice-2"
# ================================

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"✅ Login sebagai {bot.user}")
    print("📢 Bot siap digunakan!")
    await auto_join_voice()


async def auto_join_voice():
    guild = bot.get_guild(GUILD_ID)
    if guild is None:
        print("❌ Guild tidak ditemukan untuk auto-join voice.")
        return

    channel = discord.utils.get(guild.voice_channels, name=AUTO_JOIN_CHANNEL)
    if channel is None:
        print(f"❌ Voice channel '{AUTO_JOIN_CHANNEL}' tidak ditemukan.")
        return

    if guild.voice_client:
        await guild.voice_client.disconnect()
        await asyncio.sleep(1)

    try:
        await channel.connect()
        print(f"🔊 Bot auto-join ke: {channel.name}")
    except Exception as e:
        print(f"❌ Gagal join voice: {e}")


# ════════════════════════════════
#  EVENTS
# ════════════════════════════════

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


@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if member.id != bot.user.id:
        return
    if before.channel is not None and after.channel is None:
        print("⚠️ Bot di-disconnect dari voice, mencoba rejoin...")
        await asyncio.sleep(3)
        await auto_join_voice()


# ════════════════════════════════
#  VOICE COMMANDS
# ════════════════════════════════

@bot.command(name="join")
async def join(ctx):
    if ctx.author.voice is None:
        await ctx.send("❌ Kamu harus berada di voice channel dulu!")
        return
    channel = ctx.author.voice.channel
    if ctx.voice_client:
        await ctx.voice_client.move_to(channel)
        await ctx.send(f"🔊 Pindah ke **{channel.name}**!")
    else:
        await channel.connect()
        await ctx.send(f"🔊 Join ke **{channel.name}**!")


@bot.command(name="leave")
async def leave(ctx):
    if ctx.voice_client is None:
        await ctx.send("❌ Bot tidak sedang di voice channel!")
        return
    channel_name = ctx.voice_client.channel.name
    await ctx.voice_client.disconnect()
    await ctx.send(f"👋 Leave dari **{channel_name}**!")


# ════════════════════════════════
#  DM COMMANDS
# ════════════════════════════════

def is_founder(member: discord.Member) -> bool:
    founder_role = discord.utils.get(member.guild.roles, name="Founder")
    return founder_role in member.roles


async def get_guild_member(ctx):
    """Helper: ambil guild & member, cek founder."""
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


@bot.command(name="anc")
async def announcement(ctx, *, pesan: str = ""):
    """
    Kirim announcement ke #📢│announcement via DM.
    Bisa dengan teks saja, gambar saja, atau keduanya.
    Usage: !anc [teks] + (opsional: attach gambar)
    """
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

    # Cek ada gambar/gif atau tidak — hanya pakai URL, tidak kirim ulang sebagai file
    image_url = None
    if ctx.message.attachments:
        for att in ctx.message.attachments:
            ct = att.content_type or ""
            if ct.startswith("image/") or ct == "image/gif":
                image_url = att.url
                break  # ambil gambar pertama saja

    if image_url and pesan:
        # Kirim gambar dulu
        img_embed = discord.Embed(color=discord.Color.from_str("#5865f2"))
        img_embed.set_image(url=image_url)
        await announce_ch.send("@everyone", embed=img_embed)

        # Lalu kirim teks di bawahnya
        txt_embed = discord.Embed(
            description=pesan,
            color=discord.Color.from_str("#5865f2")
        )
        txt_embed.set_author(
            name=ctx.author.display_name,
            icon_url=ctx.author.display_avatar.url
        )
        txt_embed.set_footer(text="📢 Announcement")
        await announce_ch.send(embed=txt_embed)

    elif image_url:
        # Hanya gambar
        img_embed = discord.Embed(color=discord.Color.from_str("#5865f2"))
        img_embed.set_image(url=image_url)
        img_embed.set_footer(text="📢 Announcement")
        await announce_ch.send("@everyone", embed=img_embed)

    else:
        # Hanya teks
        txt_embed = discord.Embed(
            description=pesan,
            color=discord.Color.from_str("#5865f2")
        )
        txt_embed.set_author(
            name=ctx.author.display_name,
            icon_url=ctx.author.display_avatar.url
        )
        txt_embed.set_footer(text="📢 Announcement")
        await announce_ch.send("@everyone", embed=txt_embed)

    await ctx.send("✅ Announcement berhasil dikirim!")


@bot.command(name="rules")
async def rules(ctx, *, isi: str = ""):
    """
    Kirim rules ke channel rules via DM.
    Bisa dengan teks saja, gambar saja, atau keduanya.
    Usage: !rules [teks] + (opsional: attach gambar)
    """
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

    # Cek ada gambar/gif atau tidak — hanya pakai URL, tidak kirim ulang sebagai file
    image_url = None
    if ctx.message.attachments:
        for att in ctx.message.attachments:
            ct = att.content_type or ""
            if ct.startswith("image/") or ct == "image/gif":
                image_url = att.url
                break  # ambil gambar pertama saja

    if image_url and isi:
        # Kirim gambar dulu
        img_embed = discord.Embed(color=discord.Color.from_str("#ff7043"))
        img_embed.set_image(url=image_url)
        await rules_ch.send(embed=img_embed)

        # Lalu teks di bawahnya
        txt_embed = discord.Embed(
            title="📋 Rules Server",
            description=isi,
            color=discord.Color.from_str("#ff7043")
        )
        txt_embed.set_footer(text="Harap patuhi rules yang berlaku!")
        await rules_ch.send(embed=txt_embed)

    elif image_url:
        img_embed = discord.Embed(color=discord.Color.from_str("#ff7043"))
        img_embed.set_image(url=image_url)
        img_embed.set_footer(text="Harap patuhi rules yang berlaku!")
        await rules_ch.send(embed=img_embed)

    else:
        txt_embed = discord.Embed(
            title="📋 Rules Server",
            description=isi,
            color=discord.Color.from_str("#ff7043")
        )
        txt_embed.set_footer(text="Harap patuhi rules yang berlaku!")
        await rules_ch.send(embed=txt_embed)

    await ctx.send("✅ Rules berhasil dikirim!")


bot.run(os.environ.get("TOKEN"))


# ════════════════════════════════
#  MODRINTH API
# ════════════════════════════════

import aiohttp

MODRINTH_API = "https://api.modrinth.com/v2"
MODRINTH_HEADERS = {"User-Agent": "N4CX-Bot/1.0"}

FACET_MAP = {
    "mod":    '[["project_type:mod"]]',
    "shader": '[["project_type:shader"]]',
    "rp":     '[["project_type:resourcepack"]]',
}

LABEL_MAP = {
    "mod":    "🔧 Mod",
    "shader": "✨ Shader",
    "rp":     "📦 Resource Pack",
}


async def search_modrinth(query: str, facet_type: str):
    params = {
        "query": query,
        "facets": FACET_MAP[facet_type],
        "limit": 5,
    }
    async with aiohttp.ClientSession(headers=MODRINTH_HEADERS) as session:
        async with session.get(f"{MODRINTH_API}/search", params=params) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            return data.get("hits", [])


def make_modrinth_embed(hit: dict, facet_type: str, index: int, total: int) -> discord.Embed:
    title    = hit.get("title", "Unknown")
    desc     = hit.get("description", "No description.")
    icon_url = hit.get("icon_url")
    gallery  = hit.get("gallery", [])

    embed = discord.Embed(
        title=title,
        description=desc[:300] + ("..." if len(desc) > 300 else ""),
        color=0x1bd96a
    )

    # Gambar: utamakan gallery, fallback ke icon
    if gallery:
        embed.set_image(url=gallery[0])
    elif icon_url:
        embed.set_image(url=icon_url)

    embed.set_footer(text=f"Modrinth • {index+1}/{total} • N4CX Bot")
    return embed


class ModrinthNavView(discord.ui.View):
    def __init__(self, hits: list, facet_type: str, index: int = 0):
        super().__init__(timeout=60)
        self.hits       = hits
        self.facet_type = facet_type
        self.index      = index
        self._rebuild()

    def _rebuild(self):
        self.clear_items()
        # Download button
        slug    = self.hits[self.index].get("slug", "")
        dl_link = f"https://modrinth.com/{self.facet_type}/{slug}"
        self.add_item(discord.ui.Button(
            label="⬇️ Download",
            style=discord.ButtonStyle.link,
            url=dl_link,
            row=0
        ))
        # Prev button
        prev = discord.ui.Button(label="◀ Prev", style=discord.ButtonStyle.secondary, row=1, disabled=(self.index == 0))
        prev.callback = self._prev
        self.add_item(prev)
        # Next button
        nxt = discord.ui.Button(label="Next ▶", style=discord.ButtonStyle.secondary, row=1, disabled=(self.index >= len(self.hits) - 1))
        nxt.callback = self._next
        self.add_item(nxt)

    async def _prev(self, interaction: discord.Interaction):
        self.index -= 1
        self._rebuild()
        embed = make_modrinth_embed(self.hits[self.index], self.facet_type, self.index, len(self.hits))
        await interaction.response.edit_message(embed=embed, view=self)

    async def _next(self, interaction: discord.Interaction):
        self.index += 1
        self._rebuild()
        embed = make_modrinth_embed(self.hits[self.index], self.facet_type, self.index, len(self.hits))
        await interaction.response.edit_message(embed=embed, view=self)


@bot.command(name="mod")
async def search_mod(ctx, *, query: str = ""):
    """Cari mod di Modrinth. Usage: !mod <nama>"""
    if not query:
        await ctx.send("❌ Tulis nama mod! Contoh: `!mod sodium`")
        return
    msg  = await ctx.send(f"🔍 Mencari mod **{query}**...")
    hits = await search_modrinth(query, "mod")
    if not hits:
        await msg.edit(content=f"❌ Mod **{query}** tidak ditemukan.")
        return
    embed = make_modrinth_embed(hits[0], "mod", 0, len(hits))
    await msg.edit(content=None, embed=embed, view=ModrinthNavView(hits, "mod"))


@bot.command(name="shader")
async def search_shader(ctx, *, query: str = ""):
    """Cari shader di Modrinth. Usage: !shader <nama>"""
    if not query:
        await ctx.send("❌ Tulis nama shader! Contoh: `!shader complementary`")
        return
    msg  = await ctx.send(f"🔍 Mencari shader **{query}**...")
    hits = await search_modrinth(query, "shader")
    if not hits:
        await msg.edit(content=f"❌ Shader **{query}** tidak ditemukan.")
        return
    embed = make_modrinth_embed(hits[0], "shader", 0, len(hits))
    await msg.edit(content=None, embed=embed, view=ModrinthNavView(hits, "shader"))


@bot.command(name="rp")
async def search_rp(ctx, *, query: str = ""):
    """Cari resource pack di Modrinth. Usage: !rp <nama>"""
    if not query:
        await ctx.send("❌ Tulis nama resource pack! Contoh: `!rp faithful`")
        return
    msg  = await ctx.send(f"🔍 Mencari resource pack **{query}**...")
    hits = await search_modrinth(query, "rp")
    if not hits:
        await msg.edit(content=f"❌ Resource pack **{query}** tidak ditemukan.")
        return
    embed = make_modrinth_embed(hits[0], "rp", 0, len(hits))
    await msg.edit(content=None, embed=embed, view=ModrinthNavView(hits, "rp"))


bot.run(os.environ.get("TOKEN"))
