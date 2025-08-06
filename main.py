import discord
from discord.ext import commands
import os
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variables d'environnement
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
TEMP_ROLE_ID = int(os.getenv('TEMP_ROLE_ID', '0'))
MEN_ROLE_ID = int(os.getenv('MEN_ROLE_ID', '0'))
WOMEN_ROLE_ID = int(os.getenv('WOMEN_ROLE_ID', '0'))
MUTE_ROLE_ID = int(os.getenv('MUTE_ROLE_ID', '0'))
PRISON_ROLE_ID = int(os.getenv('PRISON_ROLE_ID', '0'))
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID', '0'))
STARTUP_CHANNEL_ID = 1401557235871649873

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='+', intents=intents)
saved_roles = {}

@bot.event
async def on_ready():
    logger.info(f"{bot.user} est connecté.")
    channel = bot.get_channel(STARTUP_CHANNEL_ID)
    if channel:
        await channel.send("✅ Le bot a redémarré avec succès.")

# HELP EMBED
@bot.command(name="helpme")
async def help_command(ctx):
    embed = discord.Embed(title="📖 Commandes Disponibles", color=0x00ffcc)
    embed.add_field(name="+men @membre", value="Vérifie un membre homme", inline=False)
    embed.add_field(name="+wom @membre", value="Vérifie un membre femme", inline=False)
    embed.add_field(name="+mute @membre", value="Mute un membre", inline=False)
    embed.add_field(name="+omar", value="Commande personnalisée", inline=False)
    embed.add_field(name="+hebs @membre", value="Enlève tous les rôles et ajoute le rôle prison", inline=False)
    embed.add_field(name="+unhebs @membre", value="Rend tous les anciens rôles sauf le rôle temporaire", inline=False)
    await ctx.send(embed=embed)

# VERIF HOMME
@bot.command(name="men")
async def verify_men(ctx, member: discord.Member):
    await verify(ctx, member, MEN_ROLE_ID)

# VERIF FEMME
@bot.command(name="wom")
async def verify_women(ctx, member: discord.Member):
    await verify(ctx, member, WOMEN_ROLE_ID)

async def verify(ctx, member, gender_role_id):
    temp_role = member.guild.get_role(TEMP_ROLE_ID)
    gender_role = member.guild.get_role(gender_role_id)

    if temp_role in member.roles:
        await member.remove_roles(temp_role)
    await member.add_roles(gender_role)
    await ctx.send(f"✅ {member.mention} a été vérifié(e) avec le rôle {gender_role.name}")

# MUTE
@bot.command(name="mute")
async def mute(ctx, member: discord.Member):
    mute_role = ctx.guild.get_role(MUTE_ROLE_ID)
    if mute_role:
        await member.add_roles(mute_role)
        await ctx.send(f"🔇 {member.mention} a été mute.")
    else:
        await ctx.send("❌ Rôle de mute introuvable.")

# OMAR
@bot.command(name="omar")
async def omar(ctx):
    await ctx.send("🧠 Omar est toujours le boss, qu’on se le dise !")

# HEBS
@bot.command(name="hebs")
async def hebs(ctx, member: discord.Member):
    # Sauvegarde des rôles (sauf @everyone et TEMP_ROLE_ID)
    saved_roles[member.id] = [role.id for role in member.roles if role.id not in [ctx.guild.default_role.id, TEMP_ROLE_ID]]

    # Supprimer tous les rôles sauf @everyone
    roles_to_remove = [role for role in member.roles if role != ctx.guild.default_role]
    await member.remove_roles(*roles_to_remove)

    # Ajouter le rôle prison
    prison_role = ctx.guild.get_role(PRISON_ROLE_ID)
    if prison_role:
        await member.add_roles(prison_role)
        await ctx.send(f"🚨 {member.mention} a été envoyé en prison.")
    else:
        await ctx.send("❌ Rôle de prison introuvable.")

# UNHEBS
@bot.command(name="unhebs")
async def unhebs(ctx, member: discord.Member):
    # Retirer rôle prison
    prison_role = ctx.guild.get_role(PRISON_ROLE_ID)
    if prison_role and prison_role in member.roles:
        await member.remove_roles(prison_role)

    # Restaurer anciens rôles (sauf TEMP_ROLE_ID)
    role_ids = saved_roles.get(member.id, [])
    roles = [ctx.guild.get_role(rid) for rid in role_ids if rid != TEMP_ROLE_ID and ctx.guild.get_role(rid)]
    
    if roles:
        await member.add_roles(*roles)
        await ctx.send(f"🔓 {member.mention} a été libéré et a retrouvé ses rôles.")
    else:
        await ctx.send(f"⚠️ Aucun rôle sauvegardé pour {member.mention}.")

bot.run(DISCORD_TOKEN)
