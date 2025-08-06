import discord
from discord.ext import commands
import os
import json

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='+', intents=intents)

PRISON_ROLE_ID = 123456789012345678  # Remplace par le vrai ID du rôle prison
VERIFICATION_ROLE_ID = 234567890123456789  # Remplace par le vrai ID du rôle de vérification
MUTE_ROLE_ID = 345678901234567890  # Remplace par le vrai ID du rôle mute
RESTART_CHANNEL_ID = 1401557235871649873
PRISON_DATA_FILE = 'prison_data.json'

def load_prison_data():
    if os.path.exists(PRISON_DATA_FILE):
        with open(PRISON_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_prison_data(data):
    with open(PRISON_DATA_FILE, 'w') as f:
        json.dump(data, f)

@bot.event
async def on_ready():
    channel = bot.get_channel(RESTART_CHANNEL_ID)
    if channel:
        embed = discord.Embed(title="🔁 Redémarrage", description="Le bot est de retour en ligne.", color=0x00ff00)
        await channel.send(embed=embed)
    print(f"Connecté en tant que {bot.user}")

@bot.command()
async def help1(ctx):
    embed = discord.Embed(title="📘 Aide", description="Voici les commandes disponibles :", color=0x3498db)
    embed.add_field(name="+help1", value="Affiche ce message", inline=False)
    embed.add_field(name="+mute @membre", value="Mute un membre", inline=False)
    embed.add_field(name="+unmute @membre", value="Unmute un membre", inline=False)
    embed.add_field(name="+hebs @membre", value="Envoie un membre en prison", inline=False)
    embed.add_field(name="+unhebs @membre", value="Libère un membre de prison", inline=False)
    embed.add_field(name="+men", value="Rôle homme", inline=False)
    embed.add_field(name="+wom", value="Rôle femme", inline=False)
    embed.add_field(name="+omar", value="Envoie une vidéo", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def mute(ctx, member: discord.Member):
    role = ctx.guild.get_role(MUTE_ROLE_ID)
    if role:
        await member.add_roles(role)
        embed = discord.Embed(description=f"🔇 {member.mention} a été mute.", color=0xe67e22)
        await ctx.send(embed=embed)

@bot.command()
async def unmute(ctx, member: discord.Member):
    role = ctx.guild.get_role(MUTE_ROLE_ID)
    if role:
        await member.remove_roles(role)
        embed = discord.Embed(description=f"🔊 {member.mention} a été unmute.", color=0x2ecc71)
        await ctx.send(embed=embed)

@bot.command()
async def men(ctx):
    role = discord.utils.get(ctx.guild.roles, name="men")
    if role:
        await ctx.author.add_roles(role)
        embed = discord.Embed(description="✅ Rôle homme ajouté.", color=0x3498db)
        await ctx.send(embed=embed)

@bot.command()
async def wom(ctx):
    role = discord.utils.get(ctx.guild.roles, name="women")
    if role:
        await ctx.author.add_roles(role)
        embed = discord.Embed(description="✅ Rôle femme ajouté.", color=0xff69b4)
        await ctx.send(embed=embed)

@bot.command()
async def omar(ctx):
    try:
        await ctx.send(file=discord.File("omar_video.mov"))
    except Exception as e:
        await ctx.send(f"❌ Impossible d’envoyer la vidéo : {e}")

@bot.command()
async def hebs(ctx, member: discord.Member):
    prison_role = ctx.guild.get_role(PRISON_ROLE_ID)
    if not prison_role:
        await ctx.send("❌ Rôle prison introuvable.")
        return

    roles_to_save = [role.id for role in member.roles if role.id != ctx.guild.default_role.id and role.id != PRISON_ROLE_ID]
    prison_data = load_prison_data()
    prison_data[str(member.id)] = roles_to_save
    save_prison_data(prison_data)

    await member.edit(roles=[prison_role])
    embed = discord.Embed(description=f"🔒 {member.mention} a été mis en prison.", color=0xff0000)
    await ctx.send(embed=embed)

@bot.command()
async def unhebs(ctx, member: discord.Member):
    prison_data = load_prison_data()
    member_id = str(member.id)

    if member_id not in prison_data:
        embed = discord.Embed(description=f"❌ {member.mention} n'était pas en prison ou les rôles sont introuvables.", color=0xe74c3c)
        await ctx.send(embed=embed)
        return

    role_ids = prison_data[member_id]
    restored_roles = [ctx.guild.get_role(role_id) for role_id in role_ids if role_id != VERIFICATION_ROLE_ID]
    await member.edit(roles=restored_roles)

    del prison_data[member_id]
    save_prison_data(prison_data)

    embed = discord.Embed(description=f"✅ {member.mention} a été libéré de prison.", color=0x2ecc71)
    await ctx.send(embed=embed)

# Lancement du bot
bot.run(os.environ['DISCORD_TOKEN'])
