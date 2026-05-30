import discord
from discord.ext import commands
from datetime import timedelta
import time
from collections import defaultdict

# ─────────────────────────────
TOKEN = "MTUxMDAxNTU3NTk1NzU3Mzc4Mw.GN-P_k.9JHO59myGi9jPPxHVUlZxiNz4cl-mfmepFXSHA"
PREFIX = "!"

MUTE_EVERYONE_MINUTOS = 60
MUTE_FLOOD_MINUTOS = 10
LINEAS_FLOOD = 20

TARGET_USER_ID = 1422649467399569528
MUTE_TARGET_ID_MINUTOS = 60

WARN_COOLDOWN = 10  # segundos anti-spam de avisos POR USUARIO
# ─────────────────────────────

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    allowed_mentions=discord.AllowedMentions.none()
)

historial_mensajes = defaultdict(list)
ultimo_warn = {}  # cooldown por usuario (antes era por canal — ese era el bug)


# ─────────────────────────────
async def aislar(member, minutos: int, razon: str):
    try:
        await member.timeout(
            timedelta(minutes=minutos),
            reason=razon
        )
        return True
    except:
        return False


async def avisar(canal, texto: str):
    try:
        await canal.send(
            texto,
            allowed_mentions=discord.AllowedMentions.none()
        )
    except:
        pass


async def warn(message, texto: str):
    """Evita spam de avisos — cooldown por usuario, no por canal"""
    now = time.time()
    user_id = message.author.id  # 👈 clave del fix: usar user_id

    if user_id in ultimo_warn:
        if now - ultimo_warn[user_id] < WARN_COOLDOWN:
            return

    ultimo_warn[user_id] = now
    await avisar(message.channel, texto)


# ─────────────────────────────
@bot.event
async def on_message(message: discord.Message):

    user = message.author

    if user.bot:
        return

    # @everyone / @here
    if message.mention_everyone:
        try:
            await message.delete()
        except:
            pass

        if isinstance(user, discord.Member):
            await aislar(user, MUTE_EVERYONE_MINUTOS, "Mass mention")

        await warn(message, "🔇 Mensaje con @everyone/@here eliminado y usuario sancionado.")
        return

    # PING A ID PROTEGIDO
    if TARGET_USER_ID in message.raw_mentions:
        try:
            await message.delete()
        except:
            pass

        if isinstance(user, discord.Member):
            await aislar(user, MUTE_TARGET_ID_MINUTOS, "Protected user ping")

        await warn(message, "🔇 Mensaje eliminado por mencionar usuario protegido.")
        return

    # FLOOD
    lineas = message.content.count("\n") + 1

    if lineas >= LINEAS_FLOOD:
        try:
            await message.delete()
        except:
            pass

        if isinstance(user, discord.Member):
            await aislar(user, MUTE_FLOOD_MINUTOS, "Flood")

        await warn(message, "🔇 Flood detectado y eliminado.")
        return

    await bot.process_commands(message)


# ─────────────────────────────
@bot.event
async def on_ready():
    print(f"Bot activo como {bot.user}")


bot.run(TOKEN)