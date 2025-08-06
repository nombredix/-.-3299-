
import discord
from discord.ext import commands
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Bot
bot = commands.Bot(command_prefix='+', intents=intents)

# Variables d'environnement
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
RESTART_CHANNEL_ID = 1401557235871649873

# Message au démarrage
@bot.event
async def on_ready():
    logger.info(f"Connecté en tant que {bot.user}")
    channel = bot.get_channel(RESTART_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="✅ Bot redémarré",
            description=f"Le bot est prêt à l’emploi ! Connecté en tant que **{bot.user}**",
            color=0x00ff00,
            timestamp=datetime.utcnow()
        )
        await channel.send(embed=embed)

# Commande: +ping
@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"La latence est de `{latency}ms`.",
        color=0x00ffcc
    )
    await ctx.send(embed=embed)

# Commande: +test
@bot.command()
async def test(ctx):
    embed = discord.Embed(
        title="✅ Test réussi",
        description="Le bot fonctionne correctement.",
        color=0x00ff00
    )
    await ctx.send(embed=embed)

# Commande: +help1
@bot.command(name='help1')
async def help_command(ctx):
    embed = discord.Embed(
        title="📜 Aide du Bot",
        description="Voici la liste des commandes disponibles :",
        color=0x3498db
    )
    embed.add_field(name="+ping", value="Affiche la latence du bot", inline=False)
    embed.add_field(name="+test", value="Vérifie si le bot est opérationnel", inline=False)
    embed.add_field(name="+omar", value="Commande personnalisée (blague ou message)", inline=False)
    embed.add_field(name="+hebs", value="Envoie le membre en prison (rôle fictif)", inline=False)
    embed.add_field(name="+unhebs", value="Libère le membre de prison", inline=False)
    embed.set_footer(text=f"Demandé par {ctx.author}", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

# Commande: +omar
@bot.command()
async def omar(ctx):
    embed = discord.Embed(
        title="🧠 Omar",
        description="La légende raconte qu'Omar comprend tout... sauf le bot 🤖",
        color=0xf39c12
    )
    await ctx.send(embed=embed)

# Commande: +hebs
@bot.command()
async def hebs(ctx, member: discord.Member = None):
    prison_role_id = int(os.getenv('PRISON_ROLE_ID', '0'))
    if not prison_role_id:
        await ctx.send("❌ Rôle de prison non défini dans les variables d’environnement.")
        return
    if member is None:
        await ctx.send("❌ Veuillez mentionner un membre.")
        return
    prison_role = ctx.guild.get_role(prison_role_id)
    if not prison_role:
        await ctx.send("❌ Rôle de prison introuvable.")
        return
    await member.add_roles(prison_role, reason=f"Hébs par {ctx.author}")
    embed = discord.Embed(
        title="🚓 Hébs!",
        description=f"{member.mention} a été envoyé en prison par {ctx.author.mention} 🧱",
        color=0xe74c3c
    )
    await ctx.send(embed=embed)

# Commande: +unhebs
@bot.command()
async def unhebs(ctx, member: discord.Member = None):
    prison_role_id = int(os.getenv('PRISON_ROLE_ID', '0'))
    if not prison_role_id:
        await ctx.send("❌ Rôle de prison non défini dans les variables d’environnement.")
        return
    if member is None:
        await ctx.send("❌ Veuillez mentionner un membre.")
        return
    prison_role = ctx.guild.get_role(prison_role_id)
    if not prison_role:
        await ctx.send("❌ Rôle de prison introuvable.")
        return
    await member.remove_roles(prison_role, reason=f"Libération par {ctx.author}")
    embed = discord.Embed(
        title="🔓 Libération",
        description=f"{member.mention} a été libéré de prison par {ctx.author.mention} 🕊️",
        color=0x2ecc71
    )
    await ctx.send(embed=embed)

# Lancement du bot
bot.run(DISCORD_TOKEN)
