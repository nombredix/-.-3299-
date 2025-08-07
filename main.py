import discord
from discord.ext import commands
import os
import sys

# ---------------- CONFIG ----------------
TOKEN = os.getenv("DISCORD_TOKEN")  # Variable d'environnement dans Render
PREFIX = "+"
PRISON_ROLE_ID = 123456789012345678  # ID du rôle prison
VERIFICATION_ROLE_ID = 987654321098765432  # ID du rôle de vérification initial
STARTUP_CHANNEL_ID = 112233445566778899  # ID du salon pour le message de démarrage

# Vérification du token
if not TOKEN:
    print("❌ ERREUR : Le token Discord n'est pas défini. Ajoute DISCORD_TOKEN dans Render.")
    sys.exit(1)

# ----------------------------------------
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# Dictionnaires pour stocker les rôles
saved_roles = {}
muted_members = {}

# ---------------- UTILS ----------------
def create_embed(title, description, color=0x3498db):
    return discord.Embed(title=title, description=description, color=color)

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

@bot.command()
async def help(ctx):
    embed = create_embed("📜 Commandes disponibles", "")
    embed.add_field(name="+ping", value="Vérifie la latence du bot", inline=False)
    embed.add_field(name="+mute <membre>", value="Retire tous les rôles d'un membre", inline=False)
    embed.add_field(name="+unmute <membre>", value="Rend ses rôles à un membre mute", inline=False)
    embed.add_field(name="+hebs <membre>", value="Envoie un membre en prison", inline=False)
    embed.add_field(name="+unhebs <membre>", value="Libère un membre de prison", inline=False)
    embed.add_field(name="+omar", value="Commande personnalisée", inline=False)
    embed.add_field(name="+test", value="Commande de test", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def test(ctx):
    await ctx.send(embed=create_embed("🧪 Test", "Le bot fonctionne correctement."))

@bot.command()
async def omar(ctx):
    await ctx.send(embed=create_embed("😎 Omar", "Omar est toujours au top."))

# ---------------- LANCEMENT ----------------
bot.run(TOKEN)
