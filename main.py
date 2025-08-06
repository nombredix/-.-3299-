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
        roles_to_save = [role.id for role in member.roles if role.id != member.guild.default_role.id and role.id != TEMP_ROLE_ID]
        self.saved_roles[member.id] = roles_to_save
        logger.info(f"Rôles sauvegardés pour {member.display_name}: {len(roles_to_save)} rôles")

    async def restore_user_roles(self, member):
        if member.id not in self.saved_roles:
            return False
        
        guild = member.guild
        roles_to_restore = [guild.get_role(role_id) for role_id in self.saved_roles[member.id] if guild.get_role(role_id)]
        
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

# Initialisation de la classe de vérification
verification_bot = VerificationBot(bot)

@bot.event
async def on_ready():
    """Événement déclenché quand le bot est prêt"""
    logger.info(f'{bot.user} est connecté et prêt!')
    
    # Afficher un message de confirmation dans un canal spécifique
    guild = bot.get_guild(GUILD_ID)
    if guild:
        channel = guild.text_channels[0]  # Vous pouvez choisir un canal spécifique
        await channel.send("💬 Le bot a démarré avec succès et est maintenant prêt à être utilisé!")

    # Vérification de la configuration
    missing_roles = []
    if not guild.get_role(TEMP_ROLE_ID):
        missing_roles.append(f"Rôle temporaire (ID: {TEMP_ROLE_ID})")
    if not guild.get_role(MEN_ROLE_ID):
        missing_roles.append(f"Rôle hommes (ID: {MEN_ROLE_ID})")
    if not guild.get_role(WOMEN_ROLE_ID):
        missing_roles.append(f"Rôle femmes (ID: {WOMEN_ROLE_ID})")
        
    if missing_roles:
        logger.warning(f"Rôles manquants: {', '.join(missing_roles)}")
        
    if not bot.get_channel(LOG_CHANNEL_ID):
        logger.warning(f"Canal de logs (ID: {LOG_CHANNEL_ID}) non trouvé")

@bot.event
async def on_member_join(member):
    """Événement déclenché quand un nouveau membre rejoint le serveur"""
    logger.info(f"Nouveau membre: {member.display_name} ({member.id})")
    
    if member.guild.id != GUILD_ID:
        return
        
    await asyncio.sleep(1)
    await verification_bot.assign_temp_role(member)

def is_admin():
    async def predicate(ctx):
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ Cette commande est réservée aux administrateurs.")
            logger.warning(f"{ctx.author.display_name} a tenté d'utiliser une commande admin sans permissions")
            return False
        return True
    return commands.check(predicate)

@bot.command(name='men')
@is_admin()
async def verify_men(ctx, member: discord.Member = None):
    if member is None and ctx.message.reference:
        try:
            replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            member = replied_message.author
        except:
            pass
    
    if member is None:
        await ctx.send("❌ Veuillez mentionner un membre ou répondre à son message.")
        return
        
    await verification_bot.verify_member(ctx, member, MEN_ROLE_ID)

@bot.command(name='wom')
@is_admin()
async def verify_women(ctx, member: discord.Member = None):
    if member is None and ctx.message.reference:
        try:
            replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            member = replied_message.author
        except:
            pass
    
    if member is None:
        await ctx.send("❌ Veuillez mentionner un membre ou répondre à son message.")
        return
        
    await verification_bot.verify_member(ctx, member, WOMEN_ROLE_ID)

@bot.command(name='mute')
@is_admin()
async def mute_member(ctx, member: discord.Member = None, *, reason="Aucune raison spécifiée"):
    if member is None and ctx.message.reference:
        try:
            replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            member = replied_message.author
        except:
            pass
    
    if member is None:
        await ctx.send("❌ Veuillez mentionner un membre ou répondre à son message.")
        return
    
    await verification_bot.apply_sanction(ctx, member, MUTE_ROLE_ID, "Mute")

@bot.command(name='hebs')
@is_admin()
async def prison_member(ctx, member: discord.Member = None, *, reason="Aucune raison spécifiée"):
    if member is None and ctx.message.reference:
        try:
            replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            member = replied_message.author
        except:
            pass
    
    if member is None:
        await ctx.send("❌ Veuillez mentionner un membre ou répondre à son message.")
        return
    
    await verification_bot.apply_sanction(ctx, member, PRISON_ROLE_ID, "Prison")

@bot.command(name='unhebs')
@is_admin()
async def unprison_member(ctx, member: discord.Member = None):
    if member is None and ctx.message.reference:
        try:
            replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            member = replied_message.author
        except:
            pass
    
    if member is None:
        await ctx.send("❌ Veuillez mentionner un membre ou répondre à son message.")
        return
    
    try:
        guild = ctx.guild
        prison_role = guild.get_role(PRISON_ROLE_ID)
        mute_role = guild.get_role(MUTE_ROLE_ID)
        
        if not (prison_role in member.roles or mute_role in member.roles):
            await ctx.send(f"⚠️ {member.mention} n'est pas en prison ou muté.")
            return
        
        roles_to_remove = []
        if prison_role in member.roles:
            roles_to_remove.append(prison_role)
        if mute_role in member.roles:
            roles_to_remove.append(mute_role)
        
        if roles_to_remove:
            await member.remove_roles(*roles_to_remove, reason=f"Libération par {ctx.author}")
        
        restored = await verification_bot.restore_user_roles(member)
        
        if restored:
            await ctx.send(f"🔓 {member.mention} a été libéré(e) et ses rôles ont été restaurés!")
        else:
            await ctx.send(f"🔓 {member.mention} a été libéré(e) mais aucun rôle sauvegardé trouvé.")
        
        await verification_bot.log_action("Libération de prison/mute", ctx.author, member)
        logger.info(f"{member.display_name} libéré(e) par {ctx.author.display_name}")
        
    except discord.Forbidden:
        await ctx.send("❌ Je n'ai pas les permissions nécessaires pour gérer les rôles de ce membre.")
        logger.error(f"Permissions insuffisantes pour libérer {member.display_name}")
        
    except Exception as e:
        await ctx.send(f"❌ Une erreur s'est produite lors de la libération: {str(e)}")
        logger.error(f"Erreur lors de la libération de {member.display_name}: {e}")

# Exécution du bot
if __name__ == "__main__":
    if DISCORD_TOKEN:
        bot.run(DISCORD_TOKEN)
    else:
        logger.error("Token Discord non configuré")
        print("❌ Token Discord non configuré")
