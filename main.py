import discord
from discord.ext import commands
import os
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging pour afficher dans la console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Utiliser StreamHandler pour afficher dans la console de Railway
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
        # Dictionnaire pour sauvegarder les rôles avant sanctions {user_id: [role_ids]}
        self.saved_roles = {}

    async def log_action(self, action, admin, member, role_assigned=None):
        """Enregistre les actions dans le canal de logs"""
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
        """Attribue le rôle temporaire à un nouveau membre"""
        try:
            guild = member.guild
            temp_role = guild.get_role(TEMP_ROLE_ID)
            
            if temp_role:
                await member.add_roles(temp_role, reason="Attribution automatique du rôle temporaire")
                logger.info(f"Rôle temporaire attribué à {member.display_name}")
                
                # Log de l'attribution automatique
                await self.log_action("Attribution automatique du rôle temporaire", guild.me, member)
                
            else:
                logger.error(f"Rôle temporaire (ID: {TEMP_ROLE_ID}) non trouvé")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'attribution du rôle temporaire: {e}")

    async def verify_member(self, ctx, member, gender_role_id):
        """Vérifie un membre et lui attribue le rôle approprié"""
        try:
            guild = ctx.guild
            temp_role = guild.get_role(TEMP_ROLE_ID)
            gender_role = guild.get_role(gender_role_id)
            
            if not gender_role:
                await ctx.send("❌ Erreur: Rôle de genre non trouvé dans la configuration.")
                return False
                
            # Vérifier si le membre a le rôle temporaire
            if temp_role and temp_role not in member.roles:
                await ctx.send(f"⚠️ {member.mention} ne possède pas le rôle temporaire. Il a peut-être déjà été vérifié.")
                return False
                
            # Supprimer le rôle temporaire s'il existe
            if temp_role and temp_role in member.roles:
                await member.remove_roles(temp_role, reason=f"Vérification par {ctx.author}")
                
            # Ajouter le rôle de genre
            await member.add_roles(gender_role, reason=f"Vérification par {ctx.author}")
            
            # Message de confirmation
            await ctx.send(f"✅ {member.mention} a été vérifié(e) avec succès et a reçu le rôle {gender_role.name}!")
            
            # Log de l'action
            await self.log_action(
                f"Vérification manuelle - Attribution du rôle {gender_role.name}",
                ctx.author,
                member,
                gender_role
            )
            
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
        """Sauvegarde les rôles d'un membre (sauf rôle temporaire)"""
        roles_to_save = []
        for role in member.roles:
            # Ignorer @everyone et le rôle temporaire
            if role.id != member.guild.default_role.id and role.id != TEMP_ROLE_ID:
                roles_to_save.append(role.id)
        
        self.saved_roles[member.id] = roles_to_save
        logger.info(f"Rôles sauvegardés pour {member.display_name}: {len(roles_to_save)} rôles")

    async def restore_user_roles(self, member):
        """Restaure les rôles sauvegardés d'un membre"""
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
        
        # Supprimer la sauvegarde après restauration
        del self.saved_roles[member.id]
        return True

    async def apply_sanction(self, ctx, member, sanction_role_id, action_name):
        """Applique une sanction (mute ou prison) à un membre"""
        try:
            guild = ctx.guild
            sanction_role = guild.get_role(sanction_role_id)
            
            if not sanction_role:
                await ctx.send(f"❌ Erreur: Rôle de {action_name} non trouvé dans la configuration.")
                return False
            
            # Vérifier si le membre a déjà ce rôle
            if sanction_role in member.roles:
                await ctx.send(f"⚠️ {member.mention} possède déjà le rôle {sanction_role.name}.")
                return False
            
            # Sauvegarder les rôles actuels
            await self.save_user_roles(member)
            
            # Supprimer tous les rôles sauf @everyone
            roles_to_remove = [role for role in member.roles if role.id != guild.default_role.id]
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove, reason=f"{action_name} par {ctx.author}")
            
            # Ajouter le rôle de sanction
            await member.add_roles(sanction_role, reason=f"{action_name} par {ctx.author}")
            
            # Message de confirmation
            await ctx.send(f"🔒 {member.mention} a été {action_name.lower()}(e) avec succès!")
            
            # Log de l'action
            await self.log_action(
                f"{action_name} appliqué(e)",
                ctx.author,
                member,
                sanction_role
            )
            
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
    
    # Vérifier la configuration
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        logger.error(f"Serveur Discord (ID: {GUILD_ID}) non trouvé")
        return
        
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
    
    # Vérifier que c'est le bon serveur
    if member.guild.id != GUILD_ID:
        return
        
    # Attendre un court délai pour s'assurer que le membre est complètement chargé
    await asyncio.sleep(1)
    
    # Attribuer le rôle temporaire
    await verification_bot.assign_temp_role(member)

# Vérification de la configuration avant le démarrage
def check_configuration():
    """Vérifie que toutes les variables d'environnement nécessaires sont configurées"""
    required_vars = {
        'DISCORD_TOKEN': DISCORD_TOKEN,
        'TEMP_ROLE_ID': TEMP_ROLE_ID,
        'MEN_ROLE_ID': MEN_ROLE_ID,
        'WOMEN_ROLE_ID': WOMEN_ROLE_ID,
        'MUTE_ROLE_ID': MUTE_ROLE_ID,
        'PRISON_ROLE_ID': PRISON_ROLE_ID,
        'LOG_CHANNEL_ID': LOG_CHANNEL_ID,
        'GUILD_ID': GUILD_ID
    }
    
    missing_vars = []
    for var_name, var_value in required_vars.items():
        if not var_value or var_value == 0:
            missing_vars.append(var_name)
    
    if missing_vars:
        logger.error(f"Variables d'environnement manquantes: {', '.join(missing_vars)}")
        print("❌ Configuration incomplète!")
        print("Variables manquantes:", ', '.join(missing_vars))
        print("Veuillez configurer le fichier .env selon l'exemple fourni.")
        return False
    
    return True

if __name__ == "__main__":
    if not check_configuration():
        exit(1)
        
    try:
        logger.info("Démarrage du bot de vérification Discord...")
        if DISCORD_TOKEN:
            bot.run(DISCORD_TOKEN)  # Railway démarrera le bot ici avec le token
        else:
            logger.error("Token Discord non configuré")
            print("❌ Token Discord non configuré")
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du bot: {e}")
        print(f"❌ Erreur: {e}")
