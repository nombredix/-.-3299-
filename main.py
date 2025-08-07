import discord
from discord.ext import commands
import os

# ---------------- CONFIG ----------------
TOKEN = os.getenv("DISCORD_TOKEN")  # Stocké dans les variables d'environnement Render
PREFIX = "+"
PRISON_ROLE_ID = 123456789012345678  # ID du rôle prison
VERIFICATION_ROLE_ID = 987654321098765432  # ID du rôle de vérification initial
STARTUP_CHANNEL_ID = 112233445566778899  # ID du salon où envoyer le message de démarrage

# ----------------------------------------

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# Dictionnaire pour stocker les rôles retirés lors du +hebs
saved_roles = {}
# Dictionnaire pour stocker les rôles retirés lors du +mute
muted_members = {}

# ---------------- UTILS ----------------
def create_embed(title, description, color=0x3498db):
    embed = discord.Embed(title=title, description=description, color=color)
    return embed

# ---------------- EVENTS ----------------
@bot.event
async def on_ready():
    print(f"✅ Bot connecté en tant que {bot.user}")
    channel = bot.get_channel(STARTUP_CHANNEL_ID)
    if channel:
        await channel.send(embed=create_embed("🚀 Bot démarré", f"{bot.user.name} est maintenant en ligne !"))

# ---------------- COMMANDES ----------------
@bot.command()
async def ping(ctx):
    await ctx.send(embed=create_embed("🏓 Pong", f"Latence : {round(bot.latency * 1000)}ms"))

@bot.command()
async def mute(ctx, member: discord.Member):
    if member.id in muted_members:
        await ctx.send(embed=create_embed("⚠️ Erreur", f"{member.mention} est déjà mute.", color=0xe74c3c))
        return

    muted_members[member.id] = [role for role in member.roles if role != ctx.guild.default_role]
    await member.edit(roles=[])
    await ctx.send(embed=create_embed("🔇 Mute", f"{member.mention} a été mute."))

@bot.command()
async def unmute(ctx, member: discord.Member):
    if member.id not in muted_members:
        await ctx.send(embed=create_embed("⚠️ Erreur", f"{member.mention} n'est pas mute.", color=0xe74c3c))
        return

    roles_to_restore = muted_members.pop(member.id)
    await member.edit(roles=roles_to_restore)
    await ctx.send(embed=create_embed("🔊 Unmute", f"{member.mention} a été unmute."))

@bot.command()
async def hebs(ctx, member: discord.Member):
    prison_role = ctx.guild.get_role(PRISON_ROLE_ID)
    if not prison_role:
        await ctx.send(embed=create_embed("❌ Erreur", "Rôle prison introuvable.", color=0xe74c3c))
        return

    saved_roles[member.id] = [role for role in member.roles if role != ctx.guild.default_role and role != prison_role]
    await member.edit(roles=[prison_role])
    await ctx.send(embed=create_embed("🚫 Hebs", f"{member.mention} a été envoyé en prison."))

@bot.command()
async def unhebs(ctx, member: discord.Member):
    if member.id not in saved_roles:
        await ctx.send(embed=create_embed("⚠️ Erreur", f"{member.mention} n'est pas en prison.", color=0xe74c3c))
        return

    roles_to_restore = [role for role in saved_roles.pop(member.id) if role.id != VERIFICATION_ROLE_ID]
    await member.edit(roles=roles_to_restore)
    await ctx.send(embed=create_embed("✅ Libération", f"{member.mention} a été libéré."))

# ---------------- START BOT ----------------
bot.run(TOKEN)
