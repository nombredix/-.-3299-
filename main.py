import discord
from discord.ext import commands
import os
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration du bot
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='+', intents=intents)

# Variables d'environnement
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
TEMP_ROLE_ID = int(os.getenv('TEMP_ROLE_ID', '0'))
MEN_ROLE_ID = int(os.getenv('MEN_ROLE_ID', '0'))
WOMEN_ROLE_ID = int(os.getenv('WOMEN_ROLE_ID', '0'))
MUTE_ROLE_ID = int(os.getenv('MUTE_ROLE_ID', '0'))
PRISON_ROLE_ID = int(os.getenv('PRISON_ROLE_ID', '0'))
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID', '0'))
GUILD_ID = int(os.getenv('GUILD_ID', '0'))

class VerificationBot:
    def __init__(self, bot):
        self.bot = bot
        self.saved_roles = {}
        
    async def log_action(self, action, admin, member, role_assigned=None):
        try:
            log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                embed = discord.Embed(
                    title="📋 Action de Vérification",
                    color=0x00ff00 if role_assigned else 0xff9900,
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="Action", value=action, inline=False)
                embed.add_field(name="Administrateur", value=f"{admin.mention} ({admin.id})", inline=True)
                embed.add_field(name="Membre", value=f"{member.mention} ({member.id})", inline=True)
                if role_assigned:
                    embed.add_field(name="Rôle Attribué", value=role_assigned.name, inline=True)
                
                await log_channel.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Erreur lors du logging: {e}")

    async def assign_temp_role(self, member):
        try:
            guild = member.guild
            temp_role = guild.get_role(TEMP_ROLE_ID)
            if temp_role:
                await member.add_roles(temp_role, reason="Attribution automatique du rôle temporaire")
                logger.info(f"Rôle temporaire attribué à {member.display_name}")
                await self.log_action("Attribution automatique du rôle temporaire", guild.me, member)
            else:
                logger.error(f"Rôle temporaire (ID: {TEMP_ROLE_ID}) non trouvé")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'attribution du rôle temporaire: {e}")

    async def verify_member(self, ctx, member, gender_role_id):
        try:
            guild = ctx.guild
            temp_role = guild.get_role(TEMP_ROLE_ID)
            gender_role = guild.get_role(gender_role_id)
            
            if not gender_role:
                await ctx.send("❌ Erreur: Rôle de genre non trouvé dans la configuration.")
                return False
                
            if temp_role and temp_role not in member.roles:
                await ctx.send(f"⚠️ {member.mention} ne possède pas le rôle temporaire. Il a peut-être déjà été vérifié.")
                return False
                
            if temp_role and temp_role in member.roles:
                await member.remove_roles(temp_role, reason=f"Vérification par {ctx.author}")
                
            await member.add_roles(gender_role, reason=f"Vérification par {ctx.author}")
            await ctx.send(f"✅ {member.mention} a été vérifié(e) avec succès et a reçu le rôle {gender_role.name}!")
            await self.log_action(f"Vérification manuelle - Attribution du rôle {gender_role.name}", ctx.author, member, gender_role)
            logger.info(f"{member.display_name} vérifié par {ctx.author.display_name} avec le rôle {gender_role.name}")
            return True
            
        except discord.Forbidden:
            await ctx.send("❌ Je n'ai pas les permissions nécessaires pour gérer les rôles de ce membre.")
            logger.error(f"Permissions insuffisantes pour vérifier {member.display_name}")
            return False
            
        except Exception as e:
            await ctx.send(f"❌ Une erreur s'est produite lors de la vérification: {str(e)}")
            logger.error(f"Erreur lors de la vérification de {member.display_name}: {e}")
            return False

    async def save_user_roles(self, member):
        roles_to_save = []
        for role in member.roles:
            if role.id != member.guild.default_role.id and role.id != TEMP_ROLE_ID:
                roles_to_save.append(role.id)
        self.saved_roles[member.id] = roles_to_save
        logger.info(f"Rôles sauvegardés pour {member.display_name}: {len(roles_to_save)} rôles")

    async def restore_user_roles(self, member):
        if member.id not in self.saved_roles:
            return False
        
        guild = member.guild
        roles_to_restore = []
        
        for role_id in self.saved_roles[member.id]:
            role = guild.get_role(role_id)
            if role:
                roles_to_restore.append(role)
        
        if roles_to_restore:
            try:
                await member.add_roles(*roles_to_restore, reason="Restauration des rôles après sanction")
                logger.info(f"Rôles restaurés pour {member.display_name}: {len(roles_to_restore)} rôles")
            except Exception as e:
                logger.error(f"Erreur lors de la restauration des rôles pour {member.display_name}: {e}")
                return False
        
        del self.saved_roles[member.id]
        return True

    async def apply_sanction(self, ctx, member, sanction_role_id, action_name):
        try:
            guild = ctx.guild
            sanction_role = guild.get_role(sanction_role_id)
            if not sanction_role:
                await ctx.send(f"❌ Erreur: Rôle de {action_name} non trouvé dans la configuration.")
                return False
            
            if sanction_role in member.roles:
                await ctx.send(f"⚠️ {member.mention} possède déjà le rôle {sanction_role.name}.")
                return False
            
            await self.save_user_roles(member)
            roles_to_remove = [role for role in member.roles if role.id != guild.default_role.id]
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove, reason=f"{action_name} par {ctx.author}")
            
            await member.add_roles(sanction_role, reason=f"{action_name} par {ctx.author}")
            await ctx.send(f"🔒 {member.mention} a été {action_name.lower()}(e) avec succès!")
            await self.log_action(f"{action_name} appliqué(e)", ctx.author, member, sanction_role)
            logger.info(f"{member.display_name} {action_name.lower()}(e) par {ctx.author.display_name}")
            return True
            
        except discord.Forbidden:
            await ctx.send("❌ Je n'ai pas les permissions nécessaires pour gérer les rôles de ce membre.")
            logger.error(f"Permissions insuffisantes pour {action_name.lower()} {member.display_name}")
            return False
            
        except Exception as e:
            await ctx.send(f"❌ Une erreur s'est produite lors de l'application de la sanction: {str(e)}")
            logger.error(f"Erreur lors de l'application de la sanction à {member.display_name}: {e}")
            return False

# Initialisation du bot de vérification
verification_bot = VerificationBot(bot)

@bot.event
async def on_ready():
    """Message de démarrage dans un salon spécifique"""
    logger.info(f'{bot.user} est connecté et prêt!')
    channel = bot.get_channel(1401557235871649873)  # ID du salon pour le message de démarrage
    if channel:
        await channel.send("Le bot de vérification est maintenant en ligne et prêt à fonctionner !")
    else:
        logger.error("Salon de démarrage non trouvé")

# Commandes spécifiques
@bot.command(name='help1')
async def help1(ctx):
    """Commande help avec visuel en embed"""
    embed = discord.Embed(
        title="Commandes du Bot de Vérification",
        color=0x0099ff,
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="Vérification", value="+men @membre | +wom @membre", inline=False)
    embed.add_field(name="Sanctions", value="+mute @membre | +hebs @membre | +unhebs @membre", inline=False)
    embed.add_field(name="Info", value="+status | +pending", inline=False)
    embed.add_field(name="Vidéo", value="+omar", inline=False)
    await ctx.send(embed=embed)

@bot.command(name='omar')
async def omar(ctx):
    """Commande Omar - Envoie la vidéo spéciale"""
    try:
        video_path = "omar_video.mov"
        if not os.path.exists(video_path):
            await ctx.send("❌ Fichier vidéo Omar non trouvé.")
            logger.error("Fichier omar_video.mov non trouvé")
            return
        
        with open(video_path, 'rb') as video_file:
            await ctx.send(file=discord.File(video_file, filename="omar_video.mov"))
        logger.info(f"Commande +omar exécutée par {ctx.author.display_name}")
        
    except Exception as e:
        await ctx.send("❌ Erreur lors de l'envoi de la vidéo Omar.")
        logger.error(f"Erreur lors de l'exécution de la commande +omar: {e}")

@bot.command(name='hebs')
@commands.has_permissions(administrator=True)
async def prison_member(ctx, member: discord.Member = None):
    """Envoie un membre en prison"""
    if member is None:
        await ctx.send("❌ Veuillez mentionner un membre.")
        return

    try:
        # Applique le rôle prison et retire les autres
        prison_role = ctx.guild.get_role(PRISON_ROLE_ID)
        if prison_role:
            await member.add_roles(prison_role, reason="Envoyé en prison")
            roles_to_remove = [role for role in member.roles if role.id != ctx.guild.default_role.id]
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove, reason="Envoyé en prison")
            await ctx.send(f"🔒 {member.mention} a été envoyé en prison.")
        else:
            await ctx.send("❌ Le rôle prison est introuvable.")
    except Exception as e:
        await ctx.send(f"❌ Erreur lors de l'application de la sanction : {str(e)}")

@bot.command(name='unhebs')
@commands.has_permissions(administrator=True)
async def unprison_member(ctx, member: discord.Member = None):
    """Libère un membre de prison et restaure ses rôles"""
    if member is None:
        await ctx.send("❌ Veuillez mentionner un membre.")
        return

    try:
        prison_role = ctx.guild.get_role(PRISON_ROLE_ID)
        if prison_role in member.roles:
            await member.remove_roles(prison_role, reason="Libéré de prison")
        else:
            await ctx.send(f"⚠️ {member.mention} n'est pas en prison.")
            return
        
        restored = await verification_bot.restore_user_roles(member)
        if restored:
            await ctx.send(f"🔓 {member.mention} a été libéré(e) et ses rôles ont été restaurés!")
        else:
            await ctx.send(f"🔓 {member.mention} a été libéré(e) mais aucun rôle sauvegardé trouvé.")
    except Exception as e:
        await ctx.send(f"❌ Erreur lors de la libération : {str(e)}")

@bot.command(name='mute')
@commands.has_permissions(administrator=True)
async def mute_member(ctx, member: discord.Member = None, *, reason="Aucune raison spécifiée"):
    """Mute un membre"""
    if member is None:
        await ctx.send("❌ Veuillez mentionner un membre.")
        return

    try:
        mute_role = ctx.guild.get_role(MUTE_ROLE_ID)
        if mute_role:
            await member.add_roles(mute_role, reason=reason)
            await ctx.send(f"🔇 {member.mention} a été muté pour : {reason}")
        else:
            await ctx.send("❌ Le rôle mute est introuvable.")
    except Exception as e:
        await ctx.send(f"❌ Erreur lors de l'application du mute : {str(e)}")

@bot.command(name='unmute')
@commands.has_permissions(administrator=True)
async def unmute_member(ctx, member: discord.Member = None):
    """Unmute un membre"""
    if member is None:
        await ctx.send("❌ Veuillez mentionner un membre.")
        return

    try:
        mute_role = ctx.guild.get_role(MUTE_ROLE_ID)
        if mute_role in member.roles:
            await member.remove_roles(mute_role, reason="Unmute")
            await ctx.send(f"🔊 {member.mention} a été unmuté.")
        else:
            await ctx.send(f"⚠️ {member.mention} n'est pas muté.")
    except Exception as e:
        await ctx.send(f"❌ Erreur lors de l'annulation du mute : {str(e)}")

bot.run(DISCORD_TOKEN)
